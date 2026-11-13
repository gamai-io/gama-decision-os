#!/usr/bin/env python3
"""
Calibration Evaluator for RLDF.
Calculates Expected Calibration Error (ECE) and Brier Score over binned probabilities.
Supports pure-Python fallback to avoid strict numpy dependencies.
"""
import sys
import json
import argparse
import math

def calculate_brier_score(probabilities, labels):
    """
    Calculates Brier Score: 1/N * sum((p_i - y_i)^2)
    """
    n = len(probabilities)
    if n == 0:
        return 0.0
    
    squared_errors = [(p - y) ** 2 for p, y in zip(probabilities, labels)]
    return sum(squared_errors) / n

def calculate_ece(probabilities, labels, num_bins=10):
    """
    Calculates Expected Calibration Error (ECE):
    ECE = sum(|B_m|/N * |acc(B_m) - conf(B_m)|)
    """
    n = len(probabilities)
    if n == 0:
        return 0.0
    
    ece = 0.0
    bin_boundaries = [i / num_bins for i in range(num_bins + 1)]
    
    # Store predictions in bins
    bins = {i: [] for i in range(num_bins)}
    for p, y in zip(probabilities, labels):
        # Find which bin it belongs to
        assigned = False
        for i in range(num_bins):
            if bin_boundaries[i] <= p < bin_boundaries[i+1]:
                bins[i].append((p, y))
                assigned = True
                break
        if not assigned:
            # Handle boundary p = 1.0 which goes into the last bin
            if p >= 1.0:
                bins[num_bins - 1].append((p, y))
                
    # Calculate weighted calibration error per bin
    bin_details = {}
    for i, items in bins.items():
        bin_size = len(items)
        if bin_size == 0:
            bin_details[i] = {"size": 0, "conf": 0.0, "acc": 0.0, "error": 0.0}
            continue
            
        conf_sum = sum(p for p, _ in items)
        acc_sum = sum(y for _, y in items)
        
        avg_conf = conf_sum / bin_size
        avg_acc = acc_sum / bin_size
        
        bin_error = abs(avg_acc - avg_conf)
        ece += (bin_size / n) * bin_error
        
        bin_details[i] = {
            "size": bin_size,
            "conf": avg_conf,
            "acc": avg_acc,
            "error": bin_error
        }
        
    return ece, bin_details

def print_ascii_reliability_diagram(bin_details, num_bins=10):
    """
    Draws a beautiful ASCII reliability diagram to visualize calibration.
    """
    print("\nReliability Diagram (Calibration Visualization):")
    print(" Bin Range      | Size | Conf  | Acc   | Calibration Gap & Diagram")
    print("-" * 75)
    for i in range(num_bins):
        low = i / num_bins
        high = (i + 1) / num_bins
        b_info = bin_details[i]
        size = b_info["size"]
        conf = b_info["conf"]
        acc = b_info["acc"]
        gap = b_info["error"]
        
        if size == 0:
            diagram = "[EMPTY]"
        else:
            # Scale bars
            acc_chars = int(round(acc * 20))
            conf_chars = int(round(conf * 20))
            
            bar_list = [" "] * 20
            for k in range(max(acc_chars, conf_chars)):
                if k < min(acc_chars, conf_chars):
                    bar_list[k] = "="  # Overlap (Calibrated part)
                elif k < acc_chars:
                    bar_list[k] = "A"  # Under-confident (Accuracy > Confidence)
                else:
                    bar_list[k] = "C"  # Over-confident (Confidence > Accuracy)
            diagram = "".join(bar_list)
            
        print(f" [{low:3.1f}, {high:3.1f}) | {size:4d} | {conf:5.3f} | {acc:5.3f} | [{diagram}] (Gap: {gap:5.3f})")
    print("-" * 75)
    print("Legend: '=' calibrated overlap, 'A' under-confident gap, 'C' over-confident gap")

def main():
    parser = argparse.ArgumentParser(description="Evaluate Model Calibration (ECE & Brier Score).")
    parser.add_argument("--file", type=str, help="JSON or JSONL file containing list of dicts with 'prob' and 'label' keys.")
    parser.add_argument("--bins", type=int, default=10, help="Number of bins for ECE calculation.")
    parser.add_argument("--demo", action="store_true", help="Run with synthetic demo data if no file is provided.")
    
    args = parser.parse_args()
    
    probabilities = []
    labels = []
    
    if args.file:
        try:
            with open(args.file, "r") as f:
                if args.file.endswith(".jsonl"):
                    for line in f:
                        if not line.strip():
                            continue
                        data = json.loads(line)
                        probabilities.append(float(data["prob"]))
                        labels.append(int(data["label"]))
                else:
                    data_list = json.load(f)
                    for item in data_list:
                        probabilities.append(float(item["prob"]))
                        labels.append(int(item["label"]))
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.demo or not args.file:
        print("No input file provided. Running with synthetic calibration demo dataset...")
        # Synthetic calibrated predictions + some overconfident errors (False-Success simulation)
        probabilities = [
            0.1, 0.12, 0.15, 
            0.2, 0.25, 0.28, 
            0.4, 0.45, 0.48, 
            0.6, 0.65, 0.68, 
            0.8, 0.82, 0.85, 0.89, 
            0.9, 0.92, 0.95, 0.98
        ]
        labels = [
            0, 0, 0,
            0, 1, 0,
            0, 0, 1,
            1, 1, 0,
            1, 1, 1, 0,  # overconfidence simulation
            1, 1, 1, 1
        ]
        
    n = len(probabilities)
    print(f"Loaded {n} predictions for calibration analysis.")
    
    brier = calculate_brier_score(probabilities, labels)
    ece, bin_details = calculate_ece(probabilities, labels, args.bins)
    
    print(f"\n======================================")
    print(f"📊 Calibration Metrics (Bins={args.bins})")
    print(f"======================================")
    print(f" Brier Score: {brier:7.5f} (lower is better)")
    print(f" ECE Error:   {ece:7.5f} ({ece*100:5.2f}%)")
    print(f"======================================")
    
    print_ascii_reliability_diagram(bin_details, args.bins)

if __name__ == "__main__":
    main()
