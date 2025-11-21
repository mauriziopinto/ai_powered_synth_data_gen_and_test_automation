"""API endpoints for plain-language explanations."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List
import json
from datetime import datetime

from shared.utils.explanation_generator import get_explanation_generator, Explanation

router = APIRouter(prefix="/api/explanations", tags=["explanations"])


class ExplanationManager:
    """Manages explanation broadcasting to connected clients."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.explanation_generator = get_explanation_generator()
        self.explanation_history: List[Dict[str, Any]] = []
    
    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send explanation history to new client
        await websocket.send_json({
            'type': 'history',
            'explanations': self.explanation_history
        })
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast_explanation(self, explanation: Explanation):
        """Broadcast an explanation to all connected clients."""
        explanation_data = {
            'type': 'explanation',
            'agent_name': explanation.agent_name,
            'action': explanation.action,
            'plain_language': explanation.plain_language,
            'reasoning': explanation.reasoning,
            'before_state': explanation.before_state,
            'after_state': explanation.after_state,
            'highlights': explanation.highlights,
            'timestamp': explanation.timestamp.isoformat() if explanation.timestamp else None
        }
        
        # Store in history
        self.explanation_history.append(explanation_data)
        
        # Broadcast to all connected clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(explanation_data)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_progress(self, agent_name: str, progress: float, 
                                 current_action: str, context: Dict[str, Any]):
        """Broadcast a progress update with contextual message."""
        message = self.explanation_generator.generate_progress_message(
            agent_name, progress, current_action, context
        )
        
        progress_data = {
            'type': 'progress',
            'agent_name': agent_name,
            'progress': progress,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Broadcast to all connected clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(progress_data)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_comparison(self, before: Dict[str, Any], after: Dict[str, Any],
                                   highlights: List[str] = None):
        """Broadcast a before/after comparison."""
        comparison = self.explanation_generator.generate_comparison(before, after, highlights)
        
        comparison_data = {
            'type': 'comparison',
            'comparison': comparison,
            'timestamp': datetime.now().isoformat()
        }
        
        # Broadcast to all connected clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(comparison_data)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_decision_reasoning(self, decision: str, 
                                          factors: List[Dict[str, Any]], 
                                          conclusion: str):
        """Broadcast decision reasoning."""
        reasoning = self.explanation_generator.format_decision_reasoning(
            decision, factors, conclusion
        )
        
        reasoning_data = {
            'type': 'decision_reasoning',
            'reasoning': reasoning,
            'timestamp': datetime.now().isoformat()
        }
        
        # Broadcast to all connected clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(reasoning_data)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    def clear_history(self):
        """Clear explanation history."""
        self.explanation_history = []


# Global explanation manager instance
explanation_manager = ExplanationManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time explanation updates."""
    await explanation_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            
            # Handle client commands
            try:
                message = json.loads(data)
                if message.get('command') == 'clear_history':
                    explanation_manager.clear_history()
                    await websocket.send_json({
                        'type': 'history_cleared',
                        'timestamp': datetime.now().isoformat()
                    })
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        explanation_manager.disconnect(websocket)


@router.get("/history")
async def get_explanation_history():
    """Get the history of all explanations."""
    return {
        'explanations': explanation_manager.explanation_history,
        'count': len(explanation_manager.explanation_history)
    }


@router.delete("/history")
async def clear_explanation_history():
    """Clear the explanation history."""
    explanation_manager.clear_history()
    return {'message': 'Explanation history cleared'}


@router.get("/templates")
async def get_available_templates():
    """Get all available explanation templates."""
    generator = get_explanation_generator()
    
    templates = {}
    for agent_name, template in generator.templates.items():
        templates[agent_name] = {
            'agent_name': template.agent_name,
            'actions': list(template.templates.keys())
        }
    
    return templates


@router.post("/test")
async def test_explanation(agent_name: str, action: str, context: Dict[str, Any]):
    """Test an explanation generation (for development/debugging)."""
    generator = get_explanation_generator()
    explanation = generator.generate(agent_name, action, context)
    
    return {
        'agent_name': explanation.agent_name,
        'action': explanation.action,
        'plain_language': explanation.plain_language,
        'reasoning': explanation.reasoning,
        'timestamp': explanation.timestamp.isoformat() if explanation.timestamp else None
    }


def get_explanation_manager() -> ExplanationManager:
    """Get the global explanation manager instance."""
    return explanation_manager
