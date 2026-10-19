// Calendar entry for a deadline: an iCalendar file (RFC 5545) and a Google Calendar link.
// Both are built in the browser; nothing is sent anywhere until the user opens the link.

const encoder = new TextEncoder();

// Reminders count back from the all-day event's midnight start: 9:00 three days before and
// 9:00 the day before, in the device's own time zone.
export const REMINDERS = ["-P2DT15H", "-PT15H"];

// TEXT values escape backslash, semicolon, comma and line breaks (RFC 5545, 3.3.11).
const escapeText = (s) => s.replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n");

// Lines longer than 75 octets are folded; a continuation line starts with a space, and a
// UTF-8 character is never split (RFC 5545, 3.1).
function fold(line) {
  const parts = [];
  let part = "";
  let octets = 0;
  for (const ch of line) {
    const size = encoder.encode(ch).length;
    if (octets + size > (parts.length ? 74 : 75)) {
      parts.push(part);
      part = "";
      octets = 0;
    }
    part += ch;
    octets += size;
  }
  parts.push(part);
  return parts.join("\r\n ");
}

const compact = (iso) => iso.replaceAll("-", "");
function nextDay(iso) {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}
const stamp = (date) => date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");

export function buildIcs({ date, summary, description, url, uid, now = new Date() }) {
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//DoGood-Studio//lexdays//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "BEGIN:VEVENT",
    `UID:${uid}`,
    `DTSTAMP:${stamp(now)}`,
    `DTSTART;VALUE=DATE:${compact(date)}`,
    `DTEND;VALUE=DATE:${compact(nextDay(date))}`,
    `SUMMARY:${escapeText(summary)}`,
    `DESCRIPTION:${escapeText(description)}`,
    ...(url ? [`URL:${url}`] : []),
    "TRANSP:TRANSPARENT",
    ...REMINDERS.flatMap((trigger) => [
      "BEGIN:VALARM",
      "ACTION:DISPLAY",
      `DESCRIPTION:${escapeText(summary)}`,
      `TRIGGER:${trigger}`,
      "END:VALARM",
    ]),
    "END:VEVENT",
    "END:VCALENDAR",
  ];
  return `${lines.map(fold).join("\r\n")}\r\n`;
}

// A Google Calendar link cannot carry reminders, so this event gets the user's default reminder.
export function googleCalendarUrl({ date, summary, description }) {
  const query = new URLSearchParams({
    action: "TEMPLATE",
    text: summary,
    dates: `${compact(date)}/${compact(nextDay(date))}`,
    details: description,
  });
  return `https://calendar.google.com/calendar/render?${query}`;
}
