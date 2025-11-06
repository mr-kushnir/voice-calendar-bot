"""Monitor bot logs in real-time"""
import subprocess
import sys
import time

def monitor_bot():
    """Monitor bot logs"""
    print("=" * 60)
    print("Voice Calendar Bot - Live Monitor")
    print("=" * 60)
    print("\nBot: @nlexamtestbot")
    print("Status: Running")
    print("\nWaiting for messages...")
    print("=" * 60)
    print()

    try:
        # Follow docker logs
        process = subprocess.Popen(
            ['docker-compose', 'logs', '-f', '--tail=0', 'bot'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            # Filter and format relevant log lines
            if 'INFO' in line or 'ERROR' in line or 'WARNING' in line:
                # Remove docker-compose prefix and timestamp clutter
                line = line.strip()
                if 'voice-calendar-bot' in line:
                    line = line.split('voice-calendar-bot')[1].strip()
                    if '|' in line:
                        line = ' | '.join(line.split('|')[1:]).strip()
                print(line)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        process.terminate()

if __name__ == "__main__":
    monitor_bot()
