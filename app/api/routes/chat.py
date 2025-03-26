import ollama
from fastapi import WebSocket
from fastapi.routing import APIRouter

router = APIRouter(
    tags=["chat"],
)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_input = await websocket.receive_text()

    stream = ollama.chat(
        model='llama3.1',
        messages=[{'role': 'user', 'content': user_input}],
        stream=True
    )

    try:
        for chunk in stream:
            model_output = chunk['message']['content']
            await websocket.send_text(model_output)
    except Exception as e:
        await websocket.send_text(f"Error: {e}")
    finally:
        await websocket.close()