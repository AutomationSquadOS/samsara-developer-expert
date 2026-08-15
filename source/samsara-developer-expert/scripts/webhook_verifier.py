#!/usr/bin/env python3
"""
Samsara Webhook Signature Verifier

HMAC SHA-256 signature verification for Samsara webhooks.
"""

import hmac
import hashlib
from typing import Union


class WebhookVerifier:
    """
    Verifies HMAC SHA-256 signatures for Samsara webhooks.
    """
    
    def __init__(self, webhook_secret: str):
        """
        Initialize verifier with webhook secret.
        
        Args:
            webhook_secret: Secret from Samsara webhook configuration
        """
        self.webhook_secret = webhook_secret
    
    def verify(self, payload: Union[str, bytes], signature: str) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Raw request body (string or bytes)
            signature: X-Samsara-Signature header value
        
        Returns:
            True if signature is valid
        """
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        
        # Compute expected signature
        mac = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        )
        expected_signature = mac.hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)


# Flask example
def flask_webhook_example():
    """
    Example Flask webhook endpoint with signature verification.
    """
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    verifier = WebhookVerifier(webhook_secret="your_webhook_secret")
    
    @app.route('/webhooks/samsara', methods=['POST'])
    def samsara_webhook():
        # Get signature from header
        signature = request.headers.get('X-Samsara-Signature')
        
        if not signature:
            return jsonify({'error': 'Missing signature'}), 401
        
        # Get raw payload
        payload = request.get_data()
        
        # Verify signature
        if not verifier.verify(payload, signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse and process event
        event = request.get_json()
        process_webhook_event(event)
        
        return jsonify({'received': True}), 200
    
    return app


# FastAPI example
def fastapi_webhook_example():
    """
    Example FastAPI webhook endpoint with signature verification.
    """
    from fastapi import FastAPI, Request, HTTPException, Header
    
    app = FastAPI()
    verifier = WebhookVerifier(webhook_secret="your_webhook_secret")
    
    @app.post('/webhooks/samsara')
    async def samsara_webhook(
        request: Request,
        x_samsara_signature: str = Header(None, alias='X-Samsara-Signature')
    ):
        if not x_samsara_signature:
            raise HTTPException(status_code=401, detail='Missing signature')
        
        # Get raw payload
        payload = await request.body()
        
        # Verify signature
        if not verifier.verify(payload, x_samsara_signature):
            raise HTTPException(status_code=401, detail='Invalid signature')
        
        # Parse and process event
        event = await request.json()
        await process_webhook_event(event)
        
        return {'received': True}
    
    return app


def process_webhook_event(event: dict) -> None:
    """
    Process webhook event based on type.
    
    Args:
        event: Parsed webhook event
    """
    event_type = event.get('eventType')
    data = event.get('data', {})
    
    if event_type == 'Alert':
        print(f"Alert: {data.get('alertType')} for vehicle {data.get('vehicle', {}).get('name')}")
    
    elif event_type == 'RouteStopEtaUpdated':
        print(f"ETA updated for stop {data.get('stopId')}: {data.get('estimatedArrivalTime')}")
    
    elif event_type == 'VehicleMalfunctionDetected':
        print(f"Malfunction detected on vehicle {data.get('vehicle', {}).get('name')}")
    
    elif event_type == 'VehicleMalfunctionCleared':
        print(f"Malfunction cleared on vehicle {data.get('vehicle', {}).get('name')}")
    
    else:
        print(f"Unknown event type: {event_type}")


# Example standalone usage
if __name__ == "__main__":
    import json
    
    # Example webhook payload
    webhook_secret = "test_secret_123"
    payload = json.dumps({
        "id": "event_123",
        "eventType": "Alert",
        "createdAtTime": "2025-02-03T14:30:00Z",
        "data": {
            "alertType": "speeding",
            "vehicle": {"name": "Truck 5"}
        }
    })
    
    # Compute signature (what Samsara would send)
    mac = hmac.new(
        webhook_secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    )
    signature = mac.hexdigest()
    
    # Verify
    verifier = WebhookVerifier(webhook_secret)
    is_valid = verifier.verify(payload, signature)
    
    print(f"Signature valid: {is_valid}")
    
    if is_valid:
        event = json.loads(payload)
        process_webhook_event(event)
