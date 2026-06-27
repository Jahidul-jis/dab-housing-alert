import os
import re
import json
import hashlib
import requests
from bs4 import BeautifulSoup

URL = "https://dab-lejerbo.dk/boligsoegende/tidsbegraensede-boliger/"

POSTCODES = {
    "1050","1051","1052","1053","1054","1055","1056","1057","1058","1059",
    "1060","1061","1062","1063","1064","1065","1066","1067","1068","1069",
    "1070","1071","1072","1073","1074","1100","1101","1102","1103","1104",
    "1105","1106","1107","1110","1111","1112","1113","1114","1115","1116",
    "1117","1118","1119","1120","1121","1122","1123","1124","1125","1126",
    "1127","1128","1129","1130","1131","1150","1151","1152","1153","1154",
    "1155","1156","1157","1158","1159","1160","1161","1162","1164","1165",
    "1166","1167","1168","1169","1170","1171","1172","1173","1174","1175",
    "1200","1201","1202","1203","1204","1205","1206","1207","1208","1209",
    "1210","1211","1212","1213","1214","1215","1216","1218","1219","1220",
    "1221","1250","1251","1252","1253","1254","1255","1256","1257","1259",
    "1260","1261","1263","1264","1265","1266","1267","1268","1270","1271",
    "1300","1301","1302","1303","1304","1306","1307","1308","1309","1310",
    "1311","1312","1313","1314","1315","1316","1317","1318","1319","1320",
    "1321","1322","1323","1324","1325","1326","1327","1328","1329","1350",
    "1352","1353","1354","1355","1356","1357","1358","1359","1360","1361",
    "1362","1363","1364","1365","1366","1367","1368","1369","1370","1371",
    "1400","1401","1402","1403","1406","1407","1408","1409","1410","1411",
    "1412","1413","1414","1415","1416","1417","1418","1419","1420","1421",
    "1422","1423","1424","1425","1426","1427","1428","1429","1430","1432",
    "1433","1434","1435","1436","1437","1438","1439","1440","1441","1450",
    "1451","1452","1453","1454","1455","1456","1457","1458","1459","1460",
    "1461","1462","1463","1464","1465","1466","1467","1468","1470","1471",
    "1472","1473","1550","1551","1552","1553","1554","1555","1556","1557",
    "1558","1559","1560","1561","1562","1563","1564","1567","1568","1569",
    "1570","1571","1572","1573","1574","1575","1576","1577","1600","1601",
    "1602","1603","1604","1605","1606","1607","1608","1609","1610","1611",
    "1612","1613","1614","1615","1616","1617","1618","1619","1620","1621",
    "1622","1623","1624","1631","1632","1633","1634","1635","1650","1651",
    "1652","1653","1654","1655","1656","1657","1658","1659","1660","1661",
    "1662","1663","1664","1665","1666","1667","1668","1669","1670","1671",
    "1672","1673","1674","1675","1676","1677","1699","1700","1701","1702",
    "1703","1704","1705","1706","1707","1708","1709","1710","1711","1712",
    "1714","1715","1716","1717","1718","1719","1720","1721","1722","1723",
    "1724","1725","1726","1727","1728","1729","1730","1731","1732","1733",
    "1734","1735","1736","1737","1738","1739","1749","1750","1751","1752",
    "1753","1754","1755","1756","1757","1758","1759","1760","1761","1762",
    "1763","1764","1765","1766","1770","1771","1772","1773","1774","1775",
    "1777","1799","2100","2150","2200","2300","2400","2450","2500","2610",
    "2620","2650","2700","2720","2730","2770","2860","2880"
}

SEEN_FILE = "seen.json"


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=2)


def send_telegram(message):
    bot_token = os.environ["BOT_TOKEN"]
    chat_id = os.environ["CHAT_ID"]

    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(api_url, data={
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": False
    }, timeout=20)


def fetch_page():
    headers = {
        "User-Agent": "Mozilla/5.0 apartment-alert-bot"
    }
    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def find_matching_content(html):
    soup = BeautifulSoup(html, "html.parser")

    # Start simple and robust: collect links/cards containing target postcodes.
    matches = []

    for link in soup.find_all("a", href=True):
        text = " ".join(link.get_text(" ", strip=True).split())
        href = link["href"]

        parent_text = ""
        parent = link.find_parent()
        if parent:
            parent_text = " ".join(parent.get_text(" ", strip=True).split())

        combined = f"{text} {parent_text} {href}"

        found_postcodes = sorted(set(re.findall(r"\b\d{4}\b", combined)) & POSTCODES)

        if found_postcodes:
            full_url = href if href.startswith("http") else "https://dab-lejerbo.dk" + href
            title = text or parent_text[:80] or "Temporary housing listing"

            unique_id = hashlib.sha256(full_url.encode("utf-8")).hexdigest()

            matches.append({
                "id": unique_id,
                "title": title,
                "url": full_url,
                "postcodes": found_postcodes,
                "text": parent_text[:300]
            })

    return matches


def main():
    send_telegram("✅ Test message: DAB Housing Monitor is connected and working.")
    seen = load_seen()
    html = fetch_page()
    listings = find_matching_content(html)

    new_items = [item for item in listings if item["id"] not in seen]

    for item in new_items:
        message = (
            "🏠 New DAB-Lejerbo temporary housing match!\n\n"
            f"📍 Postcode: {', '.join(item['postcodes'])}\n"
            f"📌 Title: {item['title']}\n\n"
            f"🔗 {item['url']}"
        )
        send_telegram(message)
        seen.add(item["id"])

    save_seen(seen)
    print(f"Checked DAB-Lejerbo. Found {len(listings)} matching items, {len(new_items)} new.")


if __name__ == "__main__":
    main()
