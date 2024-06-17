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
    
    
def aggregate_metrics(app, experiment):
    
    if experiment == 1:
        settings = [1, 2, 3, 4]
        results_folder = "experiments/results_exp1"
        
    elif experiment == 2:
        settings = ["method", "class", "cluster"]
        results_folder = "experiments/results_exp2"
        
    else:
        raise ValueError("experiment must be 1 or 2")
    
    dataset_df = pd.read_csv(f"experiments/csv/{app}_scan_results_processed.csv")
    
    for i in settings:
        
        if os.path.exists(os.path.join(results_folder, f"{app}_all_results_{i}.csv")):
            
            predictions_df = pd.read_csv(os.path.join(results_folder, f"{app}_all_results_{i}.csv"), header=None)
            true_labels = dataset_df['label'].tolist()
            
            precisions = np.array([])
            recalls = np.array([])
            f1_scores = np.array([])

            for _, row in predictions_df.iterrows():
                print(row.tolist())
                precision = precision_score(true_labels, row)
                recall = recall_score(true_labels, row)
                f1 = f1_score(true_labels, row)
                
                precisions = np.append(precisions, precision)
                recalls = np.append(recalls, recall)
                f1_scores = np.append(f1_scores, f1)
                
            precision = np.mean(precisions)
            recall = np.mean(recalls)
            f1 = np.mean(f1_scores)

            print(f"- Setting {i} -")
            print(f"App Precision: {precision:.2f}")
            print(f"App Recall: {recall:.2f}")
            print(f"App F1: {f1:.2f}")
            print()
            
def aggregate_mertics_global(experiment: int, exp_iter_nb: int, apps=["damnvulnerablebank", "diva-android", "DodoBank", "ovaa", "pivaa"]):
    """
    experiment: int - 1 or 2 - The experiment number
    exp_iter_nb: int - The number of times the experiment was run for each setting and app (has to be the same for all apps and settings)
    apps: list - The list of apps to aggregate the metrics for
    """
    exp_nb = exp_iter_nb
    
    if experiment == 1:
        settings = [1, 2, 3, 4]
        results_folder = "experiments/results_exp1"
        
    elif experiment == 2:
        settings = ["method", "class", "cluster"]
        results_folder = "experiments/results_exp2"
        
    else:
        raise ValueError("experiment must be 1 or 2")
    
    
    
    concatenated_true_labels = []
    for app in apps:
        dataset_df = pd.read_csv(f"experiments/csv/{app}_scan_results_processed.csv")
        true_labels = dataset_df['label'].tolist()
        concatenated_true_labels.extend(true_labels)
        
    for i in settings:
        
        accuracies = np.array([])
        precisions = np.array([])
        recalls = np.array([])
        f1_scores = np.array([])
        
        for exp_i in range(exp_nb):
            dataset_df = pd.read_csv(f"experiments/csv/{app}_scan_results_processed.csv")
            concatenated_predictions = []
            
            for app in apps:
                if os.path.exists(os.path.join(results_folder, f"{app}_all_results_{i}.csv")):
                    predictions_df = pd.read_csv(os.path.join(results_folder, f"{app}_all_results_{i}.csv"), header=None)
                    predictions = predictions_df.iloc[exp_i].tolist()
                    if predictions_df.shape[0] != exp_nb:
                        raise ValueError(f"Number of rows in {os.path.join(results_folder, f'{app}_all_results_{i}.csv')} must be {exp_nb}")
                    
                    concatenated_predictions.extend(predictions)
                else:
                    raise ValueError(f"File {os.path.join(results_folder, f'{app}_all_results_{i}.csv')} does not exist")    
                    
            concatenated_predictions = np.array(concatenated_predictions)
            
            if len(concatenated_true_labels) != len(concatenated_predictions):
                raise ValueError(f"Length of concatenated_true_labels ({len(concatenated_true_labels)}) and concatenated_predictions ({len(concatenated_predictions)}) must be the same")
            
            accuracy = accuracy_score(concatenated_true_labels, concatenated_predictions)
            precision = precision_score(concatenated_true_labels, concatenated_predictions)
            recall = recall_score(concatenated_true_labels, concatenated_predictions)
            f1 = f1_score(concatenated_true_labels, concatenated_predictions)
            
            accuracies = np.append(accuracies, accuracy)
            precisions = np.append(precisions, precision)
            recalls = np.append(recalls, recall)
            f1_scores = np.append(f1_scores, f1)
            
        accuracy = np.mean(accuracies)
        precision = np.mean(precisions)
        recall = np.mean(recalls)
        f1 = np.mean(f1_scores)
        
        print(f"- Setting {i} -")
        print(f"Global Precision: {precision:.2f}")
        print(f"Global Recall: {recall:.2f}")
        print(f"Global F1: {f1:.2f}")
        print(f"Global Accuracy: {accuracy:.2f}")
        print()                    
            
    
if __name__ == "__main__":
    #print_metrics()
    #aggregate_metrics("pivaa")
    #aggregate_mertics_global(1, 5)
    aggregate_mertics_global(1, 15)
    