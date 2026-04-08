"""
Shared Telegram delivery helper for all workspace scripts.
Logs delivery success/failure with message IDs.
"""
import subprocess
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

TG_GROUP = "-1003882622947"
TG_TOPIC_CEO = "10"
TG_TOPIC_HR = "9"
TG_TOPIC_CMO = "7"
TG_TOPIC_CTO = "8"

def send_telegram(message, topic=None, chat_id=None):
    """
    Send a Telegram message via openclaw CLI.
    Logs and returns (success: bool, message_id: str|None, error: str|None)
    """
    if chat_id:
        target = chat_id
    elif topic:
        target = f"{TG_GROUP}:{topic}"
    else:
        target = TG_GROUP

    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--channel", "telegram",
             "--target", target, "--message", message],
            capture_output=True, text=True, timeout=15
        )
        stdout = result.stdout + result.stderr
        if result.returncode == 0 and "Sent via Telegram" in stdout:
            # Extract message ID if present
            msg_id = None
            for part in stdout.split():
                if part.strip().isdigit():
                    msg_id = part.strip()
            logger.info(f"Telegram delivery OK → target={target} msg_id={msg_id}")
            return True, msg_id, None
        else:
            err = stdout.strip() or f"exit code {result.returncode}"
            logger.error(f"Telegram delivery FAILED → target={target} error={err}")
            return False, None, err
    except subprocess.TimeoutExpired:
        logger.error(f"Telegram delivery TIMEOUT → target={target}")
        return False, None, "timeout"
    except Exception as e:
        logger.error(f"Telegram delivery EXCEPTION → target={target} error={e}")
        return False, None, str(e)
