import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from scipy.spatial.distance import cdist
from sklearn.metrics import log_loss
import os

result_dir = "results"
os.makedirs(result_dir, exist_ok=True)

def generate_ellipsoid_clusters(distance, n_samples=100, cluster_std=0.5):
    np.random.seed(0)
    covariance_matrix = np.array([[cluster_std, cluster_std * 0.8], 
                                  [cluster_std * 0.8, cluster_std]])
    
    # Generate the first cluster (class 0)
    X1 = np.random.multivariate_normal(mean=[1, 1], cov=covariance_matrix, size=n_samples)
    y1 = np.zeros(n_samples)

    # Generate the second cluster (class 1)
    X2 = np.random.multivariate_normal(mean=[1, 1], cov=covariance_matrix, size=n_samples)
    
    # Shift the second cluster along the x-axis and y-axis for a given distance
    shift_vector = np.array([distance, distance])
    X2 += shift_vector
    y2 = np.ones(n_samples)

    # Combine the clusters into one dataset
    X = np.vstack((X1, X2))
    y = np.hstack((y1, y2))
    return X, y

# Function to fit logistic regression and extract coefficients
def fit_logistic_regression(X, y):
    model = LogisticRegression()
    model.fit(X, y)
    beta0 = model.intercept_[0]
    beta1, beta2 = model.coef_[0]
    return model, beta0, beta1, beta2

def do_experiments(start, end, step_num):
    # Set up experiment parameters
    shift_distances = np.linspace(start, end, step_num)  # Range of shift distances
    beta0_list, beta1_list, beta2_list = [], [], []
    slope_list, intercept_list = [], []
    loss_list, margin_widths = [], []
    sample_data = {}  # Store sample datasets and models for visualization

    n_samples = step_num
    n_cols = 2  # Fixed number of columns
    n_rows = (n_samples + n_cols - 1) // n_cols  # Calculate rows needed
    plt.figure(figsize=(20, n_rows * 10))  # Adjust figure height based on rows

    # Run experiments for each shift distance
    for i, distance in enumerate(shift_distances, 1):
        X, y = generate_ellipsoid_clusters(distance=distance)
        # Record all necessary information for each distance
        model, beta0, beta1, beta2 = fit_logistic_regression(X, y)
        beta0_list.append(beta0)
        beta1_list.append(beta1)
        beta2_list.append(beta2)

        slope = -beta1 / beta2
        intercept = -beta0 / beta2
        slope_list.append(slope)
        intercept_list.append(intercept)

        # Calculate and store logistic loss
        loss = log_loss(y, model.predict_proba(X))
        loss_list.append(loss)

        # Plot the dataset
        plt.subplot(n_rows, n_cols, i)
        plt.scatter(X[:, 0], X[:, 1], c=y, cmap="bwr", alpha=0.7)
        x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
        y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)

        # Calculate margin width between 70% confidence contours for each class
        xx, yy = np.meshgrid(np.linspace(x_min, x_max, 200), np.linspace(y_min, y_max, 200))
        Z = model.predict_proba(np.c_[xx.ravel(), yy.ravel()])[:, 1]
        Z = Z.reshape(xx.shape)

        # Calculate decision boundary slope and intercept
        plt.contour(xx, yy, Z, levels=[0.5], colors='green')
        contour_levels = [0.7, 0.8, 0.9]
        alphas = [0.05, 0.1, 0.15]  # Increasing opacity for higher confidence levels
        min_distance = None  # Initialize min_distance

        for level, alpha in zip(contour_levels, alphas):
            class_1_contour = plt.contourf(xx, yy, Z, levels=[level, 1.0], colors=['red'], alpha=alpha)
            class_0_contour = plt.contourf(xx, yy, Z, levels=[0.0, 1 - level], colors=['blue'], alpha=alpha)
            if level == 0.7:
                # Compute minimum distance between the 70% confidence contours
                try:
                    c1_paths = class_1_contour.collections[0].get_paths()
                    c0_paths = class_0_contour.collections[0].get_paths()
                    if c1_paths and c0_paths:
                        c1_vertices = np.concatenate([p.vertices for p in c1_paths])
                        c0_vertices = np.concatenate([p.vertices for p in c0_paths])
                        distances = cdist(c1_vertices, c0_vertices)
                        min_distance = np.min(distances)
                        margin_widths.append(min_distance)
                    else:
                        margin_widths.append(np.nan)
                except Exception as e:
                    margin_widths.append(np.nan)
                    print(f"Error calculating margin width at distance {distance}: {e}")

        plt.title(f"Shift Distance = {distance:.2f}", fontsize=24)
        plt.xlabel("x1")
        plt.ylabel("x2")

        # Display decision boundary equation and margin width on the plot
        equation_text = f"{beta0:.2f} + {beta1:.2f} * x1 + {beta2:.2f} * x2 = 0\nx2 = {slope:.2f} * x1 + {intercept:.2f}"
        margin_text = f"Margin Width: {min_distance:.2f}" if min_distance else "Margin Width: N/A"
        plt.text(x_min + 0.1, y_max - 1.0, equation_text, fontsize=14, color="black", ha='left',
                 bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'))
        plt.text(x_min + 0.1, y_max - 1.5, margin_text, fontsize=14, color="black", ha='left',
                 bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'))

        if i == 1:
            plt.legend(['Class 0', 'Class 1'], loc='lower right', fontsize=20)

        sample_data[distance] = (X, y, model, beta0, beta1, beta2, min_distance)

    plt.tight_layout()
    plt.savefig(f"{result_dir}/dataset.png")

    # Plot 1: Parameters vs. Shift Distance
    plt.figure(figsize=(18, 15))

    # Plot beta0
    plt.subplot(3, 3, 1)
    plt.plot(shift_distances, beta0_list, marker='o')
    plt.title("Shift Distance vs Beta0")
    plt.xlabel("Shift Distance")
    plt.ylabel("Beta0")

    # Plot beta1
    plt.subplot(3, 3, 2)
    plt.plot(shift_distances, beta1_list, marker='o', color='orange')
    plt.title("Shift Distance vs Beta1 (Coefficient for x1)")
    plt.xlabel("Shift Distance")
    plt.ylabel("Beta1")

    # Plot beta2
    plt.subplot(3, 3, 3)
    plt.plot(shift_distances, beta2_list, marker='o', color='green')
    plt.title("Shift Distance vs Beta2 (Coefficient for x2)")
    plt.xlabel("Shift Distance")
    plt.ylabel("Beta2")

    # Plot beta1 / beta2 (Slope)
    # Plot beta1 / beta2 (Slope)
    plt.subplot(3, 3, 4)
    beta1_array = np.array(beta1_list)
    beta2_array = np.array(beta2_list)

    # Add epsilon to avoid division by zero
    epsilon = 1e-8
    slopes = beta1_array / (beta2_array + epsilon)

    # Check for NaN or inf values
    valid_indices = ~np.isnan(slopes) & ~np.isinf(slopes)

    # Plot only valid data points
    plt.plot(np.array(shift_distances)[valid_indices], slopes[valid_indices], marker='o', color='red')
    plt.title("Shift Distance vs Beta1 / Beta2 (Slope)")
    plt.xlabel("Shift Distance")
    plt.ylabel("Beta1 / Beta2 (Slope)")

    # Plot beta0 / beta2 (Intercept ratio)
    plt.subplot(3, 3, 5)
    intercepts = np.array(beta0_list) / np.array(beta2_list)
    plt.plot(shift_distances, intercepts, marker='o', color='purple')
    plt.title("Shift Distance vs Beta0 / Beta2 (Intercept Ratio)")
    plt.xlabel("Shift Distance")
    plt.ylabel("Beta0 / Beta2")

    # Plot logistic loss
    plt.subplot(3, 3, 6)
    plt.plot(shift_distances, loss_list, marker='o', color='brown')
    plt.title("Shift Distance vs Logistic Loss")
    plt.xlabel("Shift Distance")
    plt.ylabel("Logistic Loss")

    # Plot margin width
    plt.subplot(3, 3, 7)
    plt.plot(shift_distances, margin_widths, marker='o', color='cyan')
    plt.title("Shift Distance vs Margin Width")
    plt.xlabel("Shift Distance")
    plt.ylabel("Margin Width")

    plt.tight_layout()
    plt.savefig(f"{result_dir}/parameters_vs_shift_distance.png")

if __name__ == "__main__":
    start = 0.25
    end = 2.0
    step_num = 8
    do_experiments(start, end, step_num)