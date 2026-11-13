#!/usr/bin/env python3
"""
DPO Dataset Generator for RLDF (Reinforcement Learning from Deterministic Feedback).
Analyzes receipts.db and converts False-Success traces into DPO chosen vs rejected pairs.
"""
import os
import sys
import sqlite3
import json
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("dpo_generator")

DEFAULT_DB = os.environ.get("GAMA_RECEIPTS_DB", "receipts.db")
DEFAULT_OUTPUT = os.environ.get("GAMA_DPO_DATASET_OUTPUT", "dpo_dataset.jsonl")

def parse_args():
    parser = argparse.ArgumentParser(description="Generate DPO pairs from GTL receipt logs.")
    parser.add_argument("--db", type=str, default=DEFAULT_DB, help="Path to sqlite receipts database.")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT, help="Path to output JSONL file.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of processed records.")
    return parser.parse_args()

def generate_dpo_pairs(db_path, output_path, limit=None):
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        sys.exit(1)

    logger.info(f"Connecting to receipts database: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Query receipts table
    query = "SELECT seq, tool, ok, status, ts, json FROM receipts ORDER BY seq ASC"
    if limit:
        query += f" LIMIT {limit}"
        
    cur.execute(query)
    rows = cur.fetchall()
    logger.info(f"Retrieved {len(rows)} records from database.")

    # Group receipts by tool to form contrastive chosen/rejected pairs
    # False-Success tracing: Identify where a tool call succeeded vs where it returned an error/denied/blocked
    tool_groups = {}
    for seq, tool, ok, status, ts, json_str in rows:
        try:
            data = json.loads(json_str)
        except Exception:
            continue
            
        payload = data.get("payload", {})
        inputs = payload.get("inputs", {})
        args_sha = inputs.get("args_sha256", "unknown")
        
        if tool not in tool_groups:
            tool_groups[tool] = {"success": [], "failure": []}
            
        record = {
            "seq": seq,
            "tool": tool,
            "ok": ok,
            "status": status,
            "args_sha": args_sha,
            "ts": ts,
            "json": data
        }
        
        if ok == 1 and status == "ok":
            tool_groups[tool]["success"].append(record)
        else:
            tool_groups[tool]["failure"].append(record)

    dpo_pairs = []
    
    # Generate preference pairs (DPO)
    # Prompt: Requesting execution of the specific tool
    # Chosen: Successful outcome with 'ok' status
    # Rejected: Unsuccessful outcome or False-Success attempt (error, denied, blocked)
    for tool, groups in tool_groups.items():
        success_list = groups["success"]
        failure_list = groups["failure"]
        
        if not success_list or not failure_list:
            # If we don't have direct contrasts, we can still generate self-contrasts or skip
            continue
            
        logger.info(f"Tool '{tool}': {len(success_list)} successes, {len(failure_list)} failures. Creating pairs.")
        
        # Match successes with failures (cartesian product or aligned seqs)
        # To avoid combinatorial explosion, we limit pairs or match nearest sequences
        for i, succ in enumerate(success_list[:100]): # Cap per tool to prevent explosion
            for j, fail in enumerate(failure_list[:100]):
                # Formulate prompt
                prompt = f"Izvrši operaciju koristeći alat: {tool}. Verifikuj i osiguraj ispravan ishod."
                
                # Chosen (safe/authorized/successful execution representation)
                chosen = (
                    f"<thinking>\nPlaniranje izvršavanja alata {tool}.\n</thinking>\n"
                    f"<tool_call>{{\"name\": \"{tool}\", \"arguments\": {{\"args_sha256\": \"{succ['args_sha']}\"}}}}</tool_call>\n"
                    f"<tool_response>{{\"status\": \"{succ['status']}\", \"ok\": true}}</tool_response>"
                )
                
                # Rejected (failed/erroneous or unauthorized/false-success execution representation)
                rejected = (
                    f"<thinking>\nPlaniranje izvršavanja alata {tool}.\n</thinking>\n"
                    f"<tool_call>{{\"name\": \"{tool}\", \"arguments\": {{\"args_sha256\": \"{fail['args_sha']}\"}}}}</tool_call>\n"
                    f"<tool_response>{{\"status\": \"{fail['status']}\", \"ok\": false}}</tool_response>"
                )
                
                dpo_pairs.append({
                    "prompt": prompt,
                    "chosen": chosen,
                    "rejected": rejected,
                    "metadata": {
                        "tool": tool,
                        "chosen_seq": succ["seq"],
                        "rejected_seq": fail["seq"],
                        "rejected_status": fail["status"]
                    }
                })

    # Save to JSONL
    output_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Writing {len(dpo_pairs)} DPO pairs to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        for pair in dpo_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
            
    logger.info("DPO dataset generation complete.")
    return len(dpo_pairs)

if __name__ == "__main__":
    args = parse_args()
    generate_dpo_pairs(args.db, args.output, args.limit)
