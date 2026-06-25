from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from chain import TicketClassification, TicketRequest, classify_ticket

app = FastAPI(title="Hackathon API")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/", response_class=HTMLResponse)
def ticket_form():
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Sort Ticket</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            max-width: 640px;
            margin: 40px auto;
            padding: 0 16px;
          }

          label {
            display: block;
            margin-top: 14px;
            font-weight: 700;
          }

          input,
          textarea,
          button {
            box-sizing: border-box;
            width: 100%;
            margin-top: 6px;
            padding: 10px;
            font: inherit;
          }

          textarea {
            min-height: 110px;
          }

          button {
            margin-top: 18px;
            cursor: pointer;
          }

          pre {
            margin-top: 20px;
            padding: 12px;
            background: #f4f4f4;
            white-space: pre-wrap;
          }
        </style>
      </head>
      <body>
        <h1>Sort Ticket</h1>
        <form id="ticket-form">
          <label for="ticket_id">Ticket ID</label>
          <input id="ticket_id" name="ticket_id" value="T-001" required>

          <label for="channel">Channel</label>
          <input id="channel" name="channel" value="app" required>

          <label for="locale">Locale</label>
          <input id="locale" name="locale" value="en" required>

          <label for="message">Message</label>
          <textarea id="message" name="message" required>I sent 5000 taka to a wrong number this morning, please help me get it back</textarea>

          <button type="submit">Submit</button>
        </form>

        <pre id="result"></pre>

        <script>
          const form = document.getElementById("ticket-form");
          const result = document.getElementById("result");

          form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const payload = Object.fromEntries(new FormData(form).entries());
            const response = await fetch("/sort-ticket", {
              method: "POST",
              headers: {
                "Content-Type": "application/json"
              },
              body: JSON.stringify(payload)
            });

            const data = await response.json();
            result.textContent = JSON.stringify(data, null, 2);
          });
        </script>
      </body>
    </html>
    """


@app.post("/sort-ticket", response_model=TicketClassification)
def sort_ticket(ticket: TicketRequest):
    return classify_ticket(ticket)
