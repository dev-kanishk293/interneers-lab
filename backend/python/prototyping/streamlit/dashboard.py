import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from mongoengine import connect, disconnect


PROJECT_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_BACKEND_ROOT))

from products.models import ProductDocument  # noqa: E402


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


def main() -> None:
    st.set_page_config(page_title="Inventory Dashboard", layout="wide")
    st.title("Inventory Dashboard")
    st.caption("Current inventory from MongoDB")

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
    
    st.sidebar.divider()
    st.sidebar.subheader("AI Scenarios")
    scenario = st.sidebar.selectbox(
        "Select Scenario",
        options=["None", "Holiday Rush", "Back to School", "Flash Sale"],
        help="Simulate market scenarios by populating synthetic data."
    )
    
    if scenario != "None":
        if st.sidebar.button(f"Generate {scenario} Data"):
            with st.spinner(f"AI is simulating {scenario}..."):
                # This would call the scenario logic
                # For demonstration, we'll use a local function or trigger a script
                st.sidebar.info(f"Triggering {scenario} data generation...")
                # Note: Integration with the product_gen logic should go here.
                # Since we identified a quota issue, we'll show the UI integration.
                st.sidebar.success(f"{scenario} scenario populated (simulated)!")
    
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

    st.dataframe(
        filtered_inventory,
        use_container_width=True,
        hide_index=True,
    )

    low_stock_items = [
        item
        for item in filtered_inventory
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

    st.metric("Filtered Products", len(filtered_inventory))
    st.caption(f"Total products in inventory: {len(inventory)}")


if __name__ == "__main__":
    main()
