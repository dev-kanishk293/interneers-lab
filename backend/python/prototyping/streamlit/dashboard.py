import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import streamlit as st
from mongoengine import connect, disconnect
from pydantic import ValidationError

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None  # type: ignore[assignment]

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]

PROJECT_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_BACKEND_ROOT))

from products.models import ProductDocument  # noqa: E402
from products.validators import ProductListValidator  # noqa: E402
from products.semantic_search import SemanticSearchIndex, keyword_search  # noqa: E402
from products.rag import ask_the_expert, load_sample_documents  # noqa: E402

def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    return start


if load_dotenv is not None:
    load_dotenv(dotenv_path=_find_repo_root(Path(__file__).resolve()) / ".env")
else:
    st.warning("`python-dotenv` is not installed; skipping .env loading.")

SCENARIO_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "Holiday Rush": {
        "description": "Toy and gift buying spikes. Fill shelves with premium, family-focused items and keep stock levels high.",
        "count": 5,
        "stock_min": 60,
        "stock_max": 120,
    },
    "Back to School": {
        "description": "Students and parents stock up on stationery, backpacks, and study helpers with reliable quantities.",
        "count": 4,
        "stock_min": 40,
        "stock_max": 80,
    },
    "Flash Sale": {
        "description": "Limited-time promotions drive demand for gadgets, so keep trendy gear in larger than normal quantities.",
        "count": 3,
        "stock_min": 30,
        "stock_max": 70,
    },
}


def _build_scenario_prompt(name: str, config: Dict[str, Any]) -> str:
    return f"""
You are a retail supply chain analyst generating synthetic inventory data for the {name} scenario.
Produce exactly {config['count']} products. Each product must include:
- name: short descriptive string
- description: narrative <= 300 characters
- category: single string
- price: float between 5.00 and 500.00
- brand: optional string
- quantity: integer between {config['stock_min']} and {config['stock_max']}
- category_ids: list of integers (can be empty)

Respond with strictly valid JSON and nothing else. The top-level object must be {{ "products": [ ... ] }}.
{config['description']}
    """


def _request_scenarios_from_gemini(config: Dict[str, Any], scenario_name: str) -> List[Dict[str, Any]]:
    if genai is None or types is None:
        raise EnvironmentError(
            "`google-genai` is not installed; install dependencies with: "
            "pip install -r backend/python/requirements.txt"
        )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY missing; set it in your environment or .env file.")

    prompt = _build_scenario_prompt(scenario_name, config)
    client = genai.Client(api_key=api_key)

    request_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.2,
        # safety_settings=[
        #     types.SafetySetting(
        #         category="HARM_CATEGORY_UNSPECIFIED",
        #         threshold="BLOCK_NONE",
        #     )
        # ],
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config=request_config,
    )

    payload = json.loads(response.text)
    validated = ProductListValidator(**payload)
    limited_products = []
    for product in validated.products[: config["count"]]:
        record = product.model_dump()
        record["quantity"] = max(
            config["stock_min"], min(int(record["quantity"]), config["stock_max"])
        )
        record["price"] = float(record["price"])
        record["category_ids"] = record.get("category_ids") or []
        limited_products.append(record)

    if not limited_products:
        raise ValueError("Gemini returned no products.")

    return limited_products


def populate_scenario_inventory(name: str) -> Tuple[int, str]:
    config = SCENARIO_DEFINITIONS[name]
    try:
        products = _request_scenarios_from_gemini(config, name)
    except EnvironmentError as err:
        return 0, str(err)
    except ValidationError as err:
        return 0, err.json()
    except Exception as err:
        return 0, f"Failed to generate scenario data: {err}"

    connect(alias="default", **_mongo_settings())
    try:
        saved = 0
        for payload in products:
            ProductDocument(**payload).save()
            saved += 1
        return saved, ""
    finally:
        disconnect(alias="default")


def _mongo_settings() -> Dict[str, Any]:
    return {
        "db": os.getenv("MONGO_DB_NAME", "interneers_lab"),
        "host": os.getenv("MONGO_HOST", "localhost"),
        "port": int(os.getenv("MONGO_PORT", "27019")),
        "username": os.getenv("MONGO_USERNAME", "root"),
        "password": os.getenv("MONGO_PASSWORD", "example"),
        "authentication_source": os.getenv("MONGO_AUTH_SOURCE", "admin"),
    }


def fetch_inventory() -> List[Dict[str, Any]]:
    connect(alias="default", **_mongo_settings())
    try:
        products = ProductDocument.objects.order_by("id")
        return [product.to_dict() for product in products]
    finally:
        disconnect(alias="default")


def create_product(data: Dict[str, Any]) -> Dict[str, Any]:
    connect(alias="default", **_mongo_settings())
    try:
        product = ProductDocument(**data)
        product.save()
        return product.to_dict()
    finally:
        disconnect(alias="default")


def remove_product_by_id(product_id: int) -> bool:
    connect(alias="default", **_mongo_settings())
    try:
        product = ProductDocument.objects(id=product_id).first()
        if not product:
            return False
        product.delete()
        return True
    finally:
        disconnect(alias="default")


def render_ask_the_expert() -> None:
    with st.expander("Ask the Expert", expanded=True):
        docs = load_sample_documents()
        doc_names = ", ".join(document["source"] for document in docs)
        st.caption(f"Knowledge base: {doc_names or 'No text files found in public/'}")

        if "expert_messages" not in st.session_state:
            st.session_state.expert_messages = [
                {
                    "role": "assistant",
                    "content": "Ask about the product manual, return policy, or vendor FAQ.",
                }
            ]

        for message in st.session_state.expert_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input(
            "Ask the expert...",
            key="ask_the_expert_input",
        )
        if question:
            st.session_state.expert_messages.append(
                {"role": "user", "content": question}
            )
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Searching uploaded documents..."):
                    try:
                        result = ask_the_expert(question, top_k=3)
                        st.markdown(result["answer"])
                        if result["sources"]:
                            source_text = ", ".join(
                                f"{source['source']} ({source['score']})"
                                for source in result["sources"]
                            )
                            st.caption(f"Sources: {source_text}")
                    except Exception as exc:
                        result = {
                            "answer": f"Ask the Expert failed: {exc}",
                            "sources": [],
                        }
                        st.error(result["answer"])

            st.session_state.expert_messages.append(
                {"role": "assistant", "content": result["answer"]}
            )


def main() -> None:
    st.set_page_config(page_title="Inventory Dashboard", layout="wide")
    st.title("Inventory Dashboard")
    st.caption("Current inventory from MongoDB")

    render_ask_the_expert()

    with st.expander("Add Product", expanded=True):
        with st.form("add_product_form"):
            name = st.text_input("Name")
            description = st.text_input("Description")
            category = st.text_input("Category")
            price = st.number_input("Price", min_value=0.01, value=1.0, step=0.5)
            brand = st.text_input("Brand")
            quantity = st.number_input("Quantity", min_value=0, value=1, step=1)
            create_clicked = st.form_submit_button("Add Product")

        if create_clicked:
            if not all(
                [
                    name.strip(),
                    description.strip(),
                    category.strip(),
                    brand.strip(),
                ]
            ):
                st.error("Name, description, category, and brand are required.")
            else:
                try:
                    created = create_product(
                        {
                            "name": name.strip(),
                            "description": description.strip(),
                            "category": category.strip(),
                            "price": float(price),
                            "brand": brand.strip(),
                            "quantity": int(quantity),
                            "category_ids": [],
                        }
                    )
                    st.success(f"Product created successfully with ID {created['id']}.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to create product: {exc}")

    with st.expander("Remove Product", expanded=False):
        with st.form("remove_product_form"):
            remove_id = st.number_input(
                "Product ID to remove",
                min_value=1,
                value=1,
                step=1,
            )
            remove_clicked = st.form_submit_button("Remove Product")

        if remove_clicked:
            try:
                deleted = remove_product_by_id(int(remove_id))
                if deleted:
                    st.success(f"Product ID {int(remove_id)} removed.")
                    st.rerun()
                else:
                    st.warning(f"Product ID {int(remove_id)} was not found.")
            except Exception as exc:
                st.error(f"Failed to remove product: {exc}")

    try:
        inventory = fetch_inventory()
    except Exception as exc:
        st.error(f"Unable to load inventory from MongoDB: {exc}")
        st.info("Verify MongoDB is running and environment variables are correct.")
        return

    if not inventory:
        st.info("No products found yet.")
        return

    categories = sorted({item.get("category", "").strip() for item in inventory if item.get("category")})
    selected_category = st.sidebar.selectbox(
        "Filter by Category",
        options=["All"] + categories,
        index=0,
    )
    stock_alert_threshold = st.sidebar.number_input(
        "Stock Alert Threshold",
        min_value=0,
        value=5,
        step=1,
    )

    if selected_category == "All":
        filtered_inventory = inventory
    else:
        filtered_inventory = [
            item for item in inventory if item.get("category") == selected_category
        ]

    search_left, search_right = st.columns(2)
    with search_left:
        keyword_query = st.text_input(
            "Keyword Search",
            placeholder="e.g., lego, blocks, stroller",
        )
    with search_right:
        semantic_query = st.text_input(
            "Semantic Search",
            placeholder='e.g., "construction toys", "gifts for toddlers"',
        )

    keyword_filtered_inventory = keyword_search(filtered_inventory, keyword_query)
    display_inventory: List[Dict[str, Any]] = keyword_filtered_inventory

    if semantic_query.strip():
        try:
            index_products = [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "category": item.get("category"),
                    "brand": item.get("brand"),
                    "price": item.get("price"),
                    "quantity": item.get("quantity"),
                    "category_ids": item.get("category_ids"),
                }
                for item in keyword_filtered_inventory
            ]
            index = SemanticSearchIndex(index_products, model_name="all-MiniLM-L6-v2")
            results = index.search(
                semantic_query,
                top_k=min(25, len(index_products)) if index_products else 25,
                min_score=0.25,
            )
            
            display_inventory = []
            for result in results:
                enriched = dict(result.product)
                enriched["semantic_score"] = round(result.score, 4)
                display_inventory.append(enriched)
        except ImportError as exc:
            st.warning(str(exc))
        except Exception as exc:
            st.error(f"Semantic search failed: {exc}")

    st.dataframe(
        display_inventory,
        use_container_width=True,
        hide_index=True,
    )

    low_stock_items = [
        item
        for item in display_inventory
        if int(item.get("quantity", 0)) < int(stock_alert_threshold)
    ]
    if low_stock_items:
        st.error(
            f"Stock Alert: {len(low_stock_items)} item(s) are below "
            f"the threshold ({int(stock_alert_threshold)})."
        )
        st.dataframe(
            low_stock_items,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("Stock Alert: No low-stock items for the selected threshold.")

    st.metric("Displayed Products", len(display_inventory))
    st.caption(f"Total products in inventory: {len(inventory)}")


if __name__ == "__main__":
    main()
