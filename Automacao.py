import openmeteo_requests
import matplotlib.pyplot as plt
import requests_cache
import pandas as pd
from retry_requests import retry
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

def enviar_email(imagem_path, destinatario):
    remetente = " "
    senha = " "
    
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = 'Gráfico de Precipitação, Chuva e Umidade do Solo'

    corpo = MIMEText("Segue o gráfico de precipitação, chuva e umidade do solo.", 'plain')
    msg.attach(corpo)

    with open(imagem_path, 'rb') as img:
        imagem = MIMEImage(img.read())
        msg.attach(imagem)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(remetente, senha)
            server.sendmail(remetente, destinatario, msg.as_string())
            print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 52.52,
    "longitude": 13.41,
    "hourly": ["precipitation_probability", "rain", "soil_moisture_9_to_27cm"]
}
responses = openmeteo.weather_api(url, params=params)

response = responses[0]
hourly = response.Hourly()
hourly_precipitation_probability = hourly.Variables(0).ValuesAsNumpy()
hourly_rain = hourly.Variables(1).ValuesAsNumpy()
hourly_soil_moisture_9_to_27cm = hourly.Variables(2).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
    start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
    end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
    freq = pd.Timedelta(seconds = hourly.Interval()),
    inclusive = "left"
)}

hourly_data["precipitation_probability"] = hourly_precipitation_probability
hourly_data["rain"] = hourly_rain
hourly_data["soil_moisture_9_to_27cm"] = hourly_soil_moisture_9_to_27cm

hourly_dataframe = pd.DataFrame(data = hourly_data)
hourly_dataframe['date'] = pd.to_datetime(hourly_dataframe['date'])

plt.figure(figsize=(10, 6))
plt.plot(hourly_dataframe['date'], hourly_dataframe['precipitation_probability'], label='Precipitation Probability (%)', marker='o')
plt.plot(hourly_dataframe['date'], hourly_dataframe['rain'], label='Rain (mm)', marker='s')
plt.plot(hourly_dataframe['date'], hourly_dataframe['soil_moisture_9_to_27cm'], label='Soil Moisture (9-27cm)', marker='^')

plt.title('Weather Metrics Over Time', fontsize=14)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Values', fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()

imagem_path = "grafico_weather.png"
plt.savefig(imagem_path)
plt.close()

destinatario = "  "
enviar_email(imagem_path, destinatario)
