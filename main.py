# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup

# --- 1. Define the structure of the incoming data ---
class KDPPayload(BaseModel):
    accountIdentifier: str
    htmlContent: str # We now expect a string of HTML

# --- 2. Initialize the FastAPI app and CORS ---
app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Create the new parsing endpoint ---
@app.post("/api/parse")
async def parse_kdp_html(payload: KDPPayload):
    """
    This endpoint receives raw KDP Royalties Estimator HTML, 
    parses it, and extracts the tabular data.
    """
    print(f"Received HTML from account: {payload.accountIdentifier}")
    print("Starting HTML parsing...")
    print(payload.htmlContent[:500])  # Print the first 500 characters for debugging

    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(payload.htmlContent, 'lxml')

    try:
        # --- NEW PARSING LOGIC ---
        extracted_data = []
        
        # Select all the rows in the table, including the header/summary row
        # Each book entry and the main summary is contained within a 'div' with class 'item'
        table_rows = soup.select("div.ui.items.no-margin.unstackable > div.item")

        for row in table_rows:
            # Find the element containing the book title or summary title (e.g., "All 5 books")
            title_element = row.select_one(".truncate-overflow")
            title = title_element.get_text(strip=True) if title_element else "Title Not Found"

            # The royalty values are in a specific row structure. We select all value columns.
            value_elements = row.select(".sixteen.wide.computer.column .row > div")

            # Extract text from each value column if it exists, otherwise default to "N/A"
            # The structure is consistent: 6 columns, first is empty, rest are the values.
            if len(value_elements) >= 6:
                ebook_royalties = value_elements[1].get_text(strip=True)
                print_royalties = value_elements[2].get_text(strip=True)
                kenp_royalties = value_elements[3].get_text(strip=True)
                total_royalties = value_elements[4].get_text(strip=True)
                total_royalties_usd = value_elements[5].get_text(strip=True)
            else:
                # Set default values if the structure isn't found
                ebook_royalties, print_royalties, kenp_royalties, total_royalties, total_royalties_usd = ["N/A"] * 5

            # Append the structured data for this row to our results list
            extracted_data.append({
                "bookTitle": title,
                "eBookRoyalties": ebook_royalties,
                "printRoyalties": print_royalties,
                "kenpRoyalties": kenp_royalties,
                "totalRoyalties": total_royalties,
                "totalRoyaltiesUSD": total_royalties_usd,
            })

        print("Successfully extracted data:")
        print(extracted_data)

        # TODO: Save the extracted_data to your database here.

        return {"status": "success", "data": extracted_data}

    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return {"status": "error", "message": str(e)}