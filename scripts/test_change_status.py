import requests

url = "http://localhost:5000/master/business/test1234/change_status"
try:
    resp = requests.post(url, json={"master_password": "test", "status": "deleted"})
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except Exception as e:
    print(e)
