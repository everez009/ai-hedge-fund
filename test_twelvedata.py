import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("TWELVEDATA_API_KEY")
print(f"TwelveData API Key: {api_key[:20]}..." if api_key else "No API key found")

if api_key and api_key != "your-twelvedata-api-key":
    print("✓ TwelveData API key is configured!")
    
    # Test the adapter
    from src.data.forex.twelvedata import TwelveDataAdapter
    
    try:
        adapter = TwelveDataAdapter(api_key=api_key)
        print("✓ TwelveDataAdapter initialized successfully")
        
        # Try to fetch some data
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        print(f"\nTesting with EURUSD...")
        prices = adapter.get_prices("EUR/USD", start_date, end_date)
        
        if prices:
            print(f"✓ Successfully fetched {len(prices)} price points")
            print(f"  Latest price: {prices[-1].close:.5f}")
        else:
            print("✗ No data retrieved")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("✗ TwelveData API key not properly configured")
