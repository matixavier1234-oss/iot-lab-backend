from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# ⚠️ REEMPLAZA esto con tu cadena de MongoDB Atlas
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://matixavier1234_db_user:TU_PASSWORD@cluster0.06sksyi.mongodb.net/iot_lab?retryWrites=true&w=majority")

client = MongoClient(MONGO_URI)
db = client["iot_lab"]
collection = db["sensores"]

@app.route("/", methods=["GET"])
def inicio():
    return jsonify({"mensaje": "API IoT Lab funcionando"}), 200

@app.route("/ttn-webhook", methods=["POST"])
def recibir_datos():
    try:
        data = request.json
        print("Datos recibidos:", data)
        
        uplink = data.get("uplink_message", {})
        decoded = uplink.get("decoded_payload", {})
        
        # Extraer datos
        avg = decoded.get("avg", 0)
        peak = decoded.get("peak", 0)
        
        # Info del gateway
        rx_metadata = uplink.get("rx_metadata", [{}])[0]
        rssi = rx_metadata.get("rssi", 0)
        snr = rx_metadata.get("snr", 0)
        
        # Documento a guardar
        documento = {
            "device_id": data.get("end_device_ids", {}).get("device_id"),
            "dev_eui": data.get("end_device_ids", {}).get("dev_eui"),
            "avg": avg,
            "peak": peak,
            "rssi": rssi,
            "snr": snr,
            "f_cnt": uplink.get("f_cnt"),
            "f_port": uplink.get("f_port"),
            "received_at": data.get("received_at"),
            "saved_at": datetime.utcnow().isoformat()
        }
        
        collection.insert_one(documento)
        print("Guardado:", documento)
        
        return jsonify({"ok": True, "guardado": True}), 200
        
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/datos", methods=["GET"])
def listar_datos():
    """Devuelve los últimos 100 registros"""
    datos = list(collection.find({}, {"_id": 0}).sort("saved_at", -1).limit(100))
    return jsonify(datos), 200

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto)