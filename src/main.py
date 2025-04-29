from src.views import collect_all_data
from src.services import cashback_analytics
from src.reports import spending_by_category
from src.utils import load_transactions

def main() -> None:
    print(collect_all_data ("21.12.2021 15:22:13"))
    print(cashback_analytics("2021", "11"))
    print(spending_by_category(load_transactions(), "Супермаркеты", "31.12.2021"))

if __name__ == "__main__":
    main()
