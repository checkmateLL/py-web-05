import aiohttp
import asyncio
import sys
import platform
from datetime import datetime, timedelta
import json
from abc import ABC, abstractmethod

class CurrencyRatesFetcher(ABC):
    @abstractmethod
    async def fetch_rates(self, date: str) -> dict:
        pass

class PrivatBankCurrencyRatesFetcher(CurrencyRatesFetcher):
    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates"

    async def fetch_rates(self, date: str) -> dict:
        async with aiohttp.ClientSession() as session:
            params = {"json": "", "date": date}
            try:
                async with session.get(self.BASE_URL, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return self._parse_response(data, date)
            except aiohttp.ClientError as e:
                print(f"Error fetching data for {date}: {str(e)}")
                return {}

    def _parse_response(self, data: dict, date: str) -> dict:
        rates = {}
        for rate in data.get("exchangeRate", []):
            if rate.get("currency") in ["EUR", "USD"]:
                rates[rate["currency"]] = {
                    "sale": rate.get("saleRate"),
                    "purchase": rate.get("purchaseRate")
                }
        return {date: rates} if rates else {}

class CurrencyRatesService:
    def __init__(self, fetcher: CurrencyRatesFetcher):
        self.fetcher = fetcher

    async def get_rates_for_days(self, days: int) -> list:
        if days < 1 or days > 10:
            raise ValueError("Number of days must be between 1 and 10")

        dates = [(datetime.now() - timedelta(days=i)).strftime("%d.%m.%Y") for i in range(days)]
        tasks = [self.fetcher.fetch_rates(date) for date in dates]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result]

def parse_args():
    if len(sys.argv) != 2:
        print("Usage: python currency-privat.py <number_of_days>")
        sys.exit(1)
    try:
        days = int(sys.argv[1])
        if days < 1 or days > 10:
            raise ValueError
        return days
    except ValueError:
        print("Error: Please provide a valid number of days (1-10)")
        sys.exit(1)

async def main():
    days = parse_args()
    fetcher = PrivatBankCurrencyRatesFetcher()
    service = CurrencyRatesService(fetcher)
    
    try:
        rates = await service.get_rates_for_days(days)
        print(json.dumps(rates, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    if sys.platform.startswith('win'):        
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())