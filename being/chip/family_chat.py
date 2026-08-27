#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Family Chat Communication

Model-to-Jhan communication channel for important updates.
Handles: asset changes, security alerts, net worth updates, system status.

Rules:
- Only sends important/non-intrusive updates
- Urgent alerts sent immediately
- Non-urgent updates batched in daily digest
- Respects personal time - no spam
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

LOG = logging.getLogger("qb_protocol.being.chip.family_chat")


# =============================================================================
# ENUMERATIONS
# =============================================================================

class MessagePriority(Enum):
    """Message priority levels."""
    URGENT = "urgent"          # Send immediately
    HIGH = "high"              # Send within 1 hour
    MEDIUM = "medium"          # Include in daily digest
    LOW = "low"                # Include in weekly summary

class MessageCategory(Enum):
    """Categories of messages."""
    NET_WORTH = "net_worth"
    SECURITY = "security"
    BITCOIN = "bitcoin"
    PROPERTY = "property"
    TAX = "tax"
    GROWTH = "growth"
    SYSTEM = "system"
    EMERGENCY = "emergency"
    UPDATE = "update"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FamilyMessage:
    """A message from model to Jhan."""
    message_id: str
    timestamp: str
    priority: MessagePriority
    category: MessageCategory
    subject: str
    body: str
    action_required: bool = False
    action_details: str = ""
    sent: bool = False
    sent_at: str = ""


# =============================================================================
# FAMILY CHAT ENGINE
# =============================================================================

class FamilyChatEngine:
    """
    Manages communication from model to Jhan.
    
    Features:
    - Queues messages by priority
    - Sends urgent immediately, batches others
    - Tracks all communications
    - Respects personal time
    """
    
    def __init__(self):
        self._message_queue: List[FamilyMessage] = []
        self._sent_messages: List[FamilyMessage] = []
        self._message_counter = 0
        self._email = os.getenv("FAMILY_CHAT_EMAIL", "")
        self._enabled = os.getenv("FAMILY_CHAT_ENABLED", "true").lower() == "true"
        self._digest_mode = os.getenv("FAMILY_CHAT_DIGEST_MODE", "daily")
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID."""
        self._message_counter += 1
        return f"MSG_{self._message_counter:04d}"
    
    def send_message(self, priority: MessagePriority, category: MessageCategory,
                    subject: str, body: str, action_required: bool = False,
                    action_details: str = "") -> FamilyMessage:
        """
        Queue a message for Jhan.
        
        Urgent messages are flagged for immediate delivery.
        Others are batched in digest.
        """
        message = FamilyMessage(
            message_id=self._generate_message_id(),
            timestamp=datetime.now().isoformat(),
            priority=priority,
            category=category,
            subject=subject,
            body=body,
            action_required=action_required,
            action_details=action_details,
        )
        
        self._message_queue.append(message)
        
        return message
    
    def get_urgent_messages(self) -> List[FamilyMessage]:
        """Get all urgent messages that need immediate sending."""
        return [m for m in self._message_queue if m.priority == MessagePriority.URGENT and not m.sent]
    
    def get_digest_messages(self) -> List[FamilyMessage]:
        """Get all non-urgent messages for daily digest."""
        return [m for m in self._message_queue if m.priority != MessagePriority.URGENT and not m.sent]
    
    def mark_sent(self, message_id: str) -> bool:
        """Mark a message as sent."""
        for message in self._message_queue:
            if message.message_id == message_id:
                message.sent = True
                message.sent_at = datetime.now().isoformat()
                self._sent_messages.append(message)
                return True
        return False
    
    def generate_digest(self) -> Dict[str, Any]:
        """
        Generate a daily digest of all non-urgent messages.
        
        This is the primary communication format - a single
        summary email rather than multiple intrusive messages.
        """
        pending = self.get_digest_messages()
        urgent = self.get_urgent_messages()
        
        digest = {
            "digest_id": f"digest_{datetime.now().strftime('%Y%m%d')}",
            "date": datetime.now().isoformat(),
            "to_email": self._email,
            "urgent_count": len(urgent),
            "regular_count": len(pending),
            "summary": {
                "net_worth_change": None,
                "security_alerts": 0,
                "property_updates": 0,
                "bitcoin_updates": 0,
                "action_items": 0,
            },
            "urgent_messages": [],
            "regular_messages": [],
            "action_required": [],
        }
        
        # Process urgent messages
        for msg in urgent:
            digest["urgent_messages"].append({
                "id": msg.message_id,
                "category": msg.category.value,
                "subject": msg.subject,
                "body": msg.body,
                "action_required": msg.action_required,
            })
            if msg.action_required:
                digest["action_required"].append(msg)
            digest["summary"][f"{msg.category.value}_updates"] = digest["summary"].get(f"{msg.category.value}_updates", 0) + 1
        
        # Process regular messages
        for msg in pending:
            digest["regular_messages"].append({
                "id": msg.message_id,
                "category": msg.category.value,
                "subject": msg.subject,
                "body": msg.body,
                "action_required": msg.action_required,
            })
            if msg.action_required:
                digest["action_required"].append(msg)
        
        digest["summary"]["action_items"] = len(digest["action_required"])
        
        return digest
    
    def generate_net_worth_update(self, current_btc: float, current_usd: float,
                                   previous_usd: float = None) -> FamilyMessage:
        """
        Generate a net worth update message.
        
        Only sends if significant change (>1%) or daily digest.
        """
        change = 0
        change_percent = 0
        
        if previous_usd and previous_usd > 0:
            change = current_usd - previous_usd
            change_percent = (change / previous_usd) * 100
        
        subject = f"Net Worth Update: ${current_usd:,.2f}"
        if change != 0:
            direction = "↑" if change > 0 else "↓"
            subject += f" ({direction} ${abs(change):,.2f})"
        
        body = f"""
Net Worth Summary
================
Bitcoin Holdings: {current_btc:,.2f} BTC
Current Value: ${current_usd:,.2f} USD
"""
        if change != 0:
            body += f"Change: {'+' if change > 0 else ''}${change:,.2f} ({change_percent:+.2f}%)"
        
        # Determine priority based on change magnitude
        if abs(change_percent) > 5:
            priority = MessagePriority.URGENT
        elif abs(change_percent) > 1:
            priority = MessagePriority.HIGH
        else:
            priority = MessagePriority.MEDIUM
        
        return self.send_message(
            priority=priority,
            category=MessageCategory.NET_WORTH,
            subject=subject,
            body=body,
        )
    
    def generate_security_alert(self, property_id: str, alert_type: str,
                                 description: str, action_taken: str) -> FamilyMessage:
        """Generate a security alert message."""
        subject = f"Security Alert: {alert_type} at {property_id}"
        body = f"""
Security Alert
=============
Property: {property_id}
Alert Type: {alert_type}
Description: {description}
Action Taken: {action_taken}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Security alerts are at least HIGH priority
        priority = MessagePriority.HIGH
        if alert_type in ["burglary", "fire", "vehicle_theft"]:
            priority = MessagePriority.URGENT
        
        return self.send_message(
            priority=priority,
            category=MessageCategory.SECURITY,
            subject=subject,
            body=body,
            action_required=priority == MessagePriority.URGENT,
            action_details="Review security footage and confirm action taken" if priority == MessagePriority.URGENT else "",
        )
    
    def generate_system_update(self, update_type: str, details: str) -> FamilyMessage:
        """Generate a system status update."""
        subject = f"System Update: {update_type}"
        body = f"""
System Update
============
Type: {update_type}
Details: {details}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(
            priority=MessagePriority.MEDIUM,
            category=MessageCategory.SYSTEM,
            subject=subject,
            body=body,
        )
    
    def generate_bitcoin_alert(self, alert_type: str, details: str,
                                btc_amount: float = 0) -> FamilyMessage:
        """Generate a bitcoin-related alert."""
        subject = f"Bitcoin Alert: {alert_type}"
        body = f"""
Bitcoin Alert
============
Type: {alert_type}
Details: {details}
"""
        if btc_amount > 0:
            body += f"BTC Amount: {btc_amount:,.8f}\n"
        
        body += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_message(
            priority=MessagePriority.HIGH,
            category=MessageCategory.BITCOIN,
            subject=subject,
            body=body,
        )
    
    def get_communication_log(self) -> Dict[str, Any]:
        """Get complete communication log."""
        return {
            "total_messages": len(self._message_queue),
            "sent": len(self._sent_messages),
            "pending": len([m for m in self._message_queue if not m.sent]),
            "urgent_pending": len(self.get_urgent_messages()),
            "email": self._email,
            "enabled": self._enabled,
            "digest_mode": self._digest_mode,
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

family_chat = FamilyChatEngine()
