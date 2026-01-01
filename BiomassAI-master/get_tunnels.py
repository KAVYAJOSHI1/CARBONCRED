from pyngrok import ngrok
try:
    tunnels = ngrok.get_tunnels()
    for t in tunnels:
        print(f"TUNNEL: {t.public_url}")
except Exception as e:
    print(f"Error: {e}")
