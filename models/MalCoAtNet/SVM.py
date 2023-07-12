import sklearn
from sklearn import svm
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
import joblib
import utils.utils as utils
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

class SVM():
    def __init__(self, weights_path, kernel,
                    C, gamma, class_weight) -> None:
        self.weights_path = weights_path
        self.clf = svm.SVC(kernel=kernel, C=C, gamma=gamma, class_weight=class_weight)
        self.scaler  = StandardScaler()
        try:
            self.clf = joblib.load(utils.ROOT_PATH + self.weights_path + '.pkl')
        except FileNotFoundError:
            pass 

    def visualize(self, X, y):
        # convert to tsne
        tsne = TSNE(n_components=2, random_state=0)
        X_2d = tsne.fit_transform(X)
        # plot the result
        target_ids = range(len(y))
        plt.figure(figsize=(6, 5))
        colors = 'r', 'g', 'b', 'c', 'm', 'y', 'k', 'w'
        for i, c, label in zip(target_ids, colors, y):
            plt.scatter(X_2d[y == i, 0], X_2d[y == i, 1], c=c, label=label)
        plt.legend()
        plt.show()

    def predict(self, x):
        x = self.scaler.transform(x)
        y_pred = self.clf.predict(x)

        
        

    def train(self, file_path, file_type):
        X_train, y_train, X_test, y_test = self.load_data(file_path, file_type)
        self.scaler.fit(X_train)
        X_train = self.scaler.transform(X_train)
        X_test = self.scaler.transform(X_test)
        self.clf.fit(X_train, y_train)
        y_pred = self.clf.predict(X_test)
        print(confusion_matrix(y_test, y_pred))
        print(classification_report(y_test, y_pred))
        self.visualize(X_train, y_train)
        joblib.dump(utils.ROOT_PATH + self.weights_path + '.pkl')

    def load_data(self, file_path, file_type):
        if file_type == 'npy':
            dataset = np.load(file_path)
        X_train, X_test, y_train, y_test = train_test_split(dataset[:, 0:-1], dataset[:, -1], test_size=0.2)
        return X_train, y_train, X_test, y_test

    def __call__(self, x):
        ret = self.clf.predict(x)
        return ret
    
if __name__ == '__main__':
    svm = SVM()
    svm.train()