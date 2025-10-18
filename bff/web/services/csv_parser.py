"""
CSV parsing service for product batch upload.

This service handles the business logic of parsing and validating
CSV files for product creation.
"""

import csv
import io
from typing import List

from common.exceptions import ValidationError
from fastapi import UploadFile

from ..schemas import ProductCreate


class CsvParserService:
    """Service for parsing CSV files and extracting product data."""

    @staticmethod
    async def parse_products_from_csv(file: UploadFile) -> List[ProductCreate]:
        """
        Parse products from a CSV file.

        The CSV file must have the following columns:
        - provider_id (UUID)
        - name (string)
        - category (medicamentos_especiales, insumos_quirurgicos, reactivos_diagnosticos, equipos_biomedicos, otros)
        - sku (string - unique identifier)
        - price (decimal)

        Args:
            file: Uploaded CSV file

        Returns:
            List of validated ProductCreate objects

        Raises:
            ValidationError: If file is not CSV, encoding is invalid, or data is malformed
        """
        # Validate file type
        if not file.filename.endswith(".csv"):
            raise ValidationError(
                "File must be a CSV file",
                details={"filename": file.filename},
            )

        try:
            # Read CSV content (utf-8-sig handles BOM automatically)
            contents = await file.read()
            csv_text = contents.decode("utf-8-sig")
            csv_file = io.StringIO(csv_text)
            csv_reader = csv.DictReader(csv_file)

            # Parse products from CSV
            products: List[ProductCreate] = []
            for row_number, row in enumerate(
                csv_reader, start=2
            ):  # start=2 because row 1 is header
                try:
                    # Build product dict with required fields
                    product_data = {
                        "provider_id": row.get("provider_id", "").strip(),
                        "name": row.get("name", "").strip(),
                        "category": row.get("category", "").strip(),
                        "sku": row.get("sku", "").strip(),
                        "price": row.get("price", "").strip(),
                    }

                    # Validate with Pydantic
                    product = ProductCreate(**product_data)
                    products.append(product)

                except (ValueError, TypeError) as e:
                    raise ValidationError(
                        f"CSV row {row_number}: Invalid data - {str(e)}",
                        details={"row": row_number, "error": str(e)},
                    )
                except Exception as e:
                    raise ValidationError(
                        f"CSV row {row_number}: {str(e)}",
                        details={"row": row_number, "error": str(e)},
                    )

            if not products:
                raise ValidationError(
                    "CSV file is empty or contains no valid products"
                )

            return products

        except UnicodeDecodeError as e:
            raise ValidationError(
                "Invalid CSV encoding. Please use UTF-8 encoding.",
                details={"error": str(e)},
            )
        except csv.Error as e:
            raise ValidationError(
                f"CSV parsing error: {str(e)}",
                details={"error": str(e)},
            )
