import requests
from xml.etree import ElementTree as ET
from sqlmodel import Session, delete
from main import engine, Currency

def import_ecb_rates():
    try:
        namespaces = {
            'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
            'ecb': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'
        }

        with Session(engine) as session:
            session.exec(delete(Currency))
            session.commit()

            # Добавление EUR
            session.add(Currency(cur="EUR", value=1.0))
            
            # Загрузка данных
            response = requests.get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml", timeout=10)
            response.raise_for_status()  # Проверка ошибок HTTP
            
            root = ET.fromstring(response.content)
            
            for cube in root.findall(".//ecb:Cube[@currency]", namespaces=namespaces):
                currency = cube.attrib["currency"]
                rate = float(cube.attrib["rate"])
                session.add(Currency(cur=currency, value=rate))
            
            session.commit()
            
        print(f"imported {len(root.findall('.//ecb:Cube[@currency]', namespaces))} currencies")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
    except ET.ParseError as e:
        print(f"Xml parsing error: {str(e)}")


if __name__ == "__main__":
    import_ecb_rates()