from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import numpy as np
import csv
import pandas as pd
import os

def print_metrics():
    all_y_true = [
        [],
        [],
    ]
    all_y = [
        [],
        [],
    ]
    
    y_true = []
    y = []
    
    if len(all_y_true) != len(all_y):
        raise ValueError("Length of all_y_true and all_y must be the same")
    
    for i in range(len(all_y_true)):
        if len(all_y_true[i]) != len(all_y[i]):
            raise ValueError(f"Length of all_y_true[{i}] ({len(all_y_true[i])}) and all_y[i] ({len(all_y[i])}) must be the same")
                             
        y_true.extend(all_y_true[i])
        y.extend(all_y[i])
    
    print(y)
    print(y_true)
    print("Accuracy: ", accuracy_score(y_true, y))
    print("Precision: ", precision_score(y_true, y, zero_division=0))
    print("Recall: ", recall_score(y_true, y, zero_division=0))
    print("F1: ", f1_score(y_true, y, zero_division=0))
    print()
    
    
def aggregate_metrics(app):
    
    settings_nb = 4
    
    dataset_df = pd.read_csv(f"experiments/csv/{app}_scan_results_processed.csv")
    
    for i in range(1, settings_nb + 1):
        
        if os.path.exists(f"experiments/results/{app}_all_results_{i}.csv"):
            
            predictions_df = pd.read_csv(f"experiments/results/{app}_all_results_{i}.csv", header=None)
            true_labels = dataset_df['label'].tolist()
            print(true_labels)
            
            precisions = np.array([])
            recalls = np.array([])

            for _, row in predictions_df.iterrows():
                precision = precision_score(true_labels, row)
                recall = recall_score(true_labels, row)
                
                precisions = np.append(precisions, precision)
                recalls = np.append(recalls, recall)
                
            precision = np.mean(precisions)
            recall = np.mean(recalls)

            print(f"- Setting {i} -")
            print(f"Global Precision: {precision:.2f}")
            print(f"Global Recall: {recall:.2f}")
            print()
    
if __name__ == "__main__":
    #print_metrics()
    aggregate_metrics("damnvulnerablebank")
    