import json
import os
import random
import sys
import subprocess

STATE_FILE = "campaign_state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        print(f"Error: {STATE_FILE} not found.")
        sys.exit(1)
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)
    print(f"State saved to {STATE_FILE}")

def roll_dice(sides, count=1):
    """Rolls a polyhedral die."""
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls)
    print(json.dumps({"action": "roll_dice", "sides": sides, "count": count, "rolls": rolls, "total": total}))
    return total

def update_hp(entity_id, amount):
    """Updates HP for a player, party member, or known NPC."""
    state = load_state()
    for entity in state.get("entities", []):
        if entity["id"] == entity_id:
            entity["current_hp"] += amount
            # Clamp HP
            if entity["current_hp"] > entity["max_hp"]:
                entity["current_hp"] = entity["max_hp"]
            if entity["current_hp"] < 0:
                entity["current_hp"] = 0
            
            save_state(state)
            print(json.dumps({"action": "update_hp", "entity": entity_id, "new_hp": entity["current_hp"]}))
            return
    print(json.dumps({"error": f"Entity {entity_id} not found."}))

def advance_time(hours):
    """Advances in-game time and checks if faction turns should trigger."""
    state = load_state()
    state["time"]["current_hour"] += hours
    
    # Handle day rollover
    while state["time"]["current_hour"] >= 24:
        state["time"]["current_hour"] -= 24
        state["time"]["current_day"] += 1
        print("A new day has dawned.")

    save_state(state)
    print(json.dumps({"action": "advance_time", "current_day": state["time"]["current_day"], "current_hour": state["time"]["current_hour"]}))
    
    # If a significant amount of time passes (e.g., a long rest = 8 hours), flag for faction update
    if hours >= 8:
        print(json.dumps({"system_event": "TRIGGER_FACTION_TURNS", "message": "Time has passed. Instruct Faction Subagents to make their moves."}))

def move_entity(entity_id, x, y):
    """Moves an entity and pushes to GitHub."""
    state = load_state()
    found = False
    for entity in state.get("entities", []):
        if entity["id"] == entity_id:
            entity["x"] = int(x)
            entity["y"] = int(y)
            found = True
            break
    if not found:
        print(json.dumps({"error": f"Entity {entity_id} not found."}))
        return
    
    save_state(state)
    print(json.dumps({"action": "move_entity", "entity": entity_id, "x": int(x), "y": int(y)}))
    
    # Git push logic
    try:
        subprocess.run(["git", "add", STATE_FILE], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", f"VTT: Moved {entity_id} to {x}, {y}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "push"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(json.dumps({"vtt_sync": "success"}))
    except subprocess.CalledProcessError as e:
        print(json.dumps({"vtt_sync": "failed", "error": str(e)}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python engine.py <command> [args...]")
        print("Commands: roll <sides> [count], update_hp <entity_id> <amount>, advance_time <hours>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "roll":
        sides = int(sys.argv[2])
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        roll_dice(sides, count)
    elif cmd == "update_hp":
        update_hp(sys.argv[2], int(sys.argv[3]))
    elif cmd == "advance_time":
        advance_time(int(sys.argv[2]))
    elif cmd == "move":
        move_entity(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(f"Unknown command: {cmd}")
