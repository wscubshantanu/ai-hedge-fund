import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.graph.workflow import create_hedge_fund_graph

router = APIRouter(tags=["Real-Time WebSockets"])

@router.websocket("/ws/debate/{ticker}")
async def debate_websocket(websocket: WebSocket, ticker: str):
    await websocket.accept()
    ticker = ticker.upper().strip()
    try:
        await websocket.send_text(json.dumps({
            "stage": "CONNECTED",
            "message": f"WebSocket stream connected for {ticker}."
        }))

        await asyncio.sleep(0.5)
        await websocket.send_text(json.dumps({
            "stage": "STAGE_1_TECHNICALS",
            "message": f"Ingesting OHLCV feeds and computing indicators for {ticker}..."
        }))

        # Run Multi-Agent Graph in thread pool
        loop = asyncio.get_event_loop()
        app = create_hedge_fund_graph()
        initial_state = {
            "ticker": ticker,
            "debate_round": 0,
            "debate_history": [],
            "bull_arguments": [],
            "bear_arguments": [],
            "logs": []
        }

        await asyncio.sleep(0.5)
        await websocket.send_text(json.dumps({
            "stage": "STAGE_2_DEBATE",
            "message": "Convening adversarial Bull vs Bear dialectic debate rounds..."
        }))

        final_state = await loop.run_in_executor(None, app.invoke, initial_state)

        # Stream Debate Rounds
        for i, (b, r) in enumerate(zip(final_state.get("bull_arguments", []), final_state.get("bear_arguments", []))):
            await websocket.send_text(json.dumps({
                "stage": f"ROUND_{i+1}",
                "round": i + 1,
                "bull": b,
                "bear": r
            }))
            await asyncio.sleep(0.3)

        # Stream Risk Assessment
        risk = final_state.get("risk_assessment", {})
        await websocket.send_text(json.dumps({
            "stage": "STAGE_3_RISK",
            "risk_assessment": risk
        }))

        # Stream Final CIO Decision
        order = final_state.get("final_order", {})
        await websocket.send_text(json.dumps({
            "stage": "STAGE_4_DECISION",
            "final_order": order
        }))

        await websocket.send_text(json.dumps({
            "stage": "COMPLETED",
            "message": f"Committee consensus finalized for {ticker}."
        }))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({
            "stage": "ERROR",
            "error": str(e)
        }))
        await websocket.close()
