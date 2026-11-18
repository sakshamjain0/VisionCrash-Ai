import re

import requests
from alert_config import get_config
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


class Sms:
    def __init__(self, source):
        self.source = source
        self.message = "This is a Message send from Vehicle Crash Detector System , An accident involving a Vehicle Crash was detected from the CCTV Footage,detailed information" \
                       " including location and image of the incident is send as the mail for reference," \
                       " Please Send the Required Forces to the Location immediately."
        self.location = "Location not received yet"
        self.default_country_code = self._normalize_country_code(
            get_config("TWILIO_DEFAULT_COUNTRY_CODE", "+91")
        )
        self.account_sid = get_config("TWILIO_ACCOUNT_SID", "")
        self.auth_token = get_config("TWILIO_AUTH_TOKEN", "")
        self.from_number = self._to_e164(get_config("TWILIO_FROM_NUMBER", ""))
        self.messaging_service_sid = get_config("TWILIO_MESSAGING_SERVICE_SID", "")
        self.fast2sms_api_key = get_config("FAST2SMS_API_KEY", "")

        # Keep FAST2SMS_NUMBERS as fallback input to avoid breaking older setups.
        raw_numbers = get_config("TWILIO_TO_NUMBERS", "") or get_config("FAST2SMS_NUMBERS", "")
        self.numbers = self._normalize_numbers(raw_numbers)

    @staticmethod
    def _normalize_country_code(raw_country_code):
        digits = "".join(ch for ch in str(raw_country_code) if ch.isdigit())
        if not digits:
            return "+91"
        return f"+{digits}"

    def _to_e164(self, raw_number):
        value = str(raw_number).strip()
        if not value:
            return ""

        if value.startswith("+"):
            digits = "".join(ch for ch in value if ch.isdigit())
            return f"+{digits}" if digits else ""

        digits = "".join(ch for ch in value if ch.isdigit())
        if not digits:
            return ""

        if digits.startswith("00") and len(digits) > 2:
            return f"+{digits[2:]}"

        if len(digits) == 10:
            return f"{self.default_country_code}{digits}"

        if 11 <= len(digits) <= 15:
            return f"+{digits}"

        return ""

    def _normalize_numbers(self, raw_numbers):
        parts = re.split(r"[,;\n]+", str(raw_numbers).strip())
        seen = set()
        normalized = []
        for part in parts:
            if not part:
                continue
            formatted = self._to_e164(part)
            if formatted and formatted not in seen:
                seen.add(formatted)
                normalized.append(formatted)
        return normalized

    def send_sms(self):
        if self.source == 0:
            self.location = "Hindustan College Of Science And Technology"
        else:
            self.location = "Hindustan College Of Science And Technology"
        verbose_message_text = (
            self.message
            + "\n Location Received :"
            + self.location
            + "\nThis is an automatically generated SMS - please do not reply to it."
            + " For any queries regarding the same, please contact the Road Safety Department"
        )
        concise_message_text = (
            "ALERT: Vehicle crash detected. "
            f"Location: {self.location}. "
            "Dispatch emergency response."
        )
        sms_mode = get_config("TWILIO_SMS_MODE", "trial-safe").lower()
        message_text = concise_message_text if sms_mode != "full" else verbose_message_text

        if not self.numbers:
            print("SMS recipient numbers are not configured")
            return False, "SMS not sent: missing TWILIO_TO_NUMBERS or FAST2SMS_NUMBERS"

        if self.account_sid and self.auth_token:
            return self._send_twilio_sms(message_text, concise_message_text)

        if self.fast2sms_api_key:
            return self._send_fast2sms(message_text)

        print("SMS provider credentials are not configured")
        return False, "SMS not sent: configure Twilio or FAST2SMS credentials"

    def _send_twilio_sms(self, message_text, concise_message_text):
        if not self.messaging_service_sid and not self.from_number:
            print("TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID is not configured")
            return False, "SMS not sent: missing TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID"

        try:
            client = Client(self.account_sid, self.auth_token)
        except Exception as exc:
            print(f"Unable to initialize Twilio client: {exc}")
            return False, f"SMS client init failed: {exc}"

        failed_messages = []
        sent_count = 0
        for number in self.numbers:
            payload = {
                "body": message_text,
                "to": number,
            }
            if self.messaging_service_sid:
                payload["messaging_service_sid"] = self.messaging_service_sid
            else:
                payload["from_"] = self.from_number

            try:
                response = client.messages.create(**payload)
                sent_count += 1
                print(f"SMS sent to {number}. SID: {response.sid}")
            except TwilioRestException as exc:
                # Twilio trial accounts may reject long multi-segment SMS with error 30044.
                if getattr(exc, "code", None) == 30044:
                    retry_payload = dict(payload)
                    retry_payload["body"] = concise_message_text
                    try:
                        response = client.messages.create(**retry_payload)
                        sent_count += 1
                        print(f"SMS sent to {number} with concise trial-safe body. SID: {response.sid}")
                        continue
                    except TwilioRestException as retry_exc:
                        failed_messages.append(f"{number}: {retry_exc.msg}")
                    except Exception as retry_exc:
                        failed_messages.append(f"{number}: {retry_exc}")
                else:
                    failed_messages.append(f"{number}: {exc.msg}")
            except Exception as exc:
                failed_messages.append(f"{number}: {exc}")

        if failed_messages:
            detail = failed_messages[0]
            if sent_count > 0:
                print(f"SMS partially sent via Twilio. Successful: {sent_count}, Failed: {len(failed_messages)}")
                return False, f"SMS partially failed: {detail}"
            print(f"SMS failed via Twilio: {detail}")
            return False, f"SMS failed: {detail}"

        print("SMS Alert Successfully Sent via Twilio")
        return True, f"SMS alert sent to {sent_count} recipient(s)"

    def _send_fast2sms(self, message_text):
        indian_numbers = []
        for number in self.numbers:
            digits = "".join(ch for ch in number if ch.isdigit())
            if digits.startswith("91") and len(digits) == 12:
                digits = digits[2:]
            if len(digits) == 10:
                indian_numbers.append(digits)

        if not indian_numbers:
            return False, "SMS not sent: FAST2SMS needs 10-digit Indian mobile numbers"

        payload = {
            "route": get_config("FAST2SMS_ROUTE", "q"),
            "message": message_text,
            "language": "english",
            "flash": "0",
            "numbers": ",".join(indian_numbers),
        }
        headers = {
            "authorization": self.fast2sms_api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            response = requests.post(
                "https://www.fast2sms.com/dev/bulkV2",
                data=payload,
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            result = response.json()
        except Exception as exc:
            print(f"SMS failed via FAST2SMS: {exc}")
            return False, f"SMS failed via FAST2SMS: {exc}"

        if result.get("return") is True:
            print("SMS Alert Successfully Sent via FAST2SMS")
            return True, f"SMS alert sent to {len(indian_numbers)} recipient(s)"

        error = result.get("message") or result
        print(f"SMS failed via FAST2SMS: {error}")
        return False, f"SMS failed via FAST2SMS: {error}"

    def run_sms(self):
        return self.send_sms()
