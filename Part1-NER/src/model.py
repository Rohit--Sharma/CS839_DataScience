import nltk
import numpy as np
import pandas as pd
from preprocess import get_file_numbers, label_dataset
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
from sklearn import tree
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support


# TODO: Write a common method which predicts taking into consideration white list along with predictions returned by model and use it to predict everywhere
white_list = ['New York', 'Los Angeles']


def train_decision_tree(X_train, y_train, X_test, y_test):
	"""
	Trains a decision tree model on the training data and returns the accuracy on the testing data
	:param X_train: ndarray, feature vectors for candidates for training
	:param y_train: list, class labels for training
	:param X_test: ndarray, feature vectors for candidates for testing
	:param y_test: list, class labels for testing
	:return: (float, float, float, int), precision, recall, fbeta_score, support
	"""
	dt_clf = tree.DecisionTreeClassifier()
	dt_clf.fit(X_train, y_train)
	predictions = dt_clf.predict(X_test)
	return precision_recall_fscore_support(y_test, predictions, average='binary')		# dt_clf.score(X_test, y_test),


def train_random_forest(X_train, y_train, X_test, y_test):
	"""
	Trains a random forest model on the training data and returns the accuracy on the testing data
	:param X_train: ndarray, feature vectors for candidates for training
	:param y_train: list, class labels for training
	:param X_test: ndarray, feature vectors for candidates for testing
	:param y_test: list, class labels for testing
	:return: (float, float, float, int), precision, recall, fbeta_score, support
	"""
	randomforest_clf = RandomForestClassifier(n_estimators=100, max_depth=2, random_state=0)
	randomforest_clf.fit(X_train, y_train)
	predictions = randomforest_clf.predict(X_test)
	return precision_recall_fscore_support(y_test, predictions, average='binary')  # randomforest_clf.score(X_test, y_test)


def train_logistic_regression(X_train, y_train, X_test, y_test):
	"""
	Trains a logistic regression model on the training data and returns the accuracy on the testing data
	:param X_train: ndarray, feature vectors for candidates for training
	:param y_train: list, class labels for training
	:param X_test: ndarray, feature vectors for candidates for testing
	:param y_test: list, class labels for testing
	:return: (float, float, float, int), precision, recall, fbeta_score, support
	"""
	logistic_clf = LogisticRegression(solver='liblinear')
	logistic_clf.fit(X_train, y_train)
	predictions = logistic_clf.predict(X_test)
	return precision_recall_fscore_support(y_test, predictions, average='binary')  # logistic_clf.score(X_test, y_test)


def train_svm(X_train, y_train, actual_candidates, X_test, y_test):
	"""
	Trains n SVM model on the training data and returns the accuracy on the testing data
	:param X_train: ndarray, feature vectors for candidates for training
	:param y_train: list, class labels for training
	:param X_test: ndarray, feature vectors for candidates for testing
	:param y_test: list, class labels for training
	:return: (float, float, float, int), precision, recall, fbeta_score, support
	"""
	class_wts = 'balanced'	# {0: 1, 1: 10000}
	svm_clf = SVC(gamma='scale')
	svm_clf.fit(X_train, y_train)
	predictions = svm_clf.predict(X_test)

	# White list the predictions
	for idx, candidate in zip(range(len(actual_candidates)), actual_candidates):
		if candidate in white_list:
			predictions[idx] = 1
	
	#find_false_positives(actual_candidates, y_test, predictions)
	return precision_recall_fscore_support(y_test, predictions, average='binary')  # svm_clf.score(X_test, y_test)


def find_false_positives(actual_candidates, y_test, predictions):
	for i in range(0, len(predictions)):
		if predictions[i] != y_test[i]:
			print(actual_candidates[i] + " pred->" + str(predictions[i]) +" actual->" + str(y_test[i]))


def cross_validation(dev_set, n_folds):
	kf = KFold(n_splits=n_folds)
	kf.get_n_splits(dev_set)
	print('## Running Cross Validation: ##')
	dt_prec = dt_rec = 0
	rf_prec = rf_rec = 0
	lr_prec = lr_rec = 0
	svm_prec = svm_rec = 0
	for train_indices, validation_indices in kf.split(dev_set):
		train_points = []
		validation_points = []
		for idx in train_indices:
			train_points.append(dev_set[idx])
		for idx in validation_indices:
			validation_points.append(dev_set[idx])

		train_set = label_dataset(train_points, True)
		np.savetxt("train.csv", np.column_stack((train_set[0], train_set[1])), delimiter=",")
		validation_set = label_dataset(validation_points, False)

		prec, rec, f1, supp = train_decision_tree(train_set[0], train_set[1], validation_set[0], validation_set[1])
		dt_prec += prec
		dt_rec += rec

		prec, rec, f1, supp = train_random_forest(train_set[0], train_set[1], validation_set[0], validation_set[1])
		rf_prec += prec
		rf_rec += rec

		prec, rec, f1, supp = train_logistic_regression(train_set[0], train_set[1], validation_set[0], validation_set[1])
		lr_prec += prec
		lr_rec += rec

		prec, rec, f1, supp = train_svm(train_set[0], train_set[1], validation_set[2], validation_set[0], validation_set[1])
		svm_prec += prec
		svm_rec += rec

	dt_prec /= n_folds
	dt_rec /= n_folds
	dt_f1 = 2 * dt_prec * dt_rec / (dt_prec + dt_rec)

	best_f1 = dt_f1
	best_model = 'Decision Tree'

	rf_prec /= n_folds
	rf_rec /= n_folds
	rf_f1 = 2 * rf_prec * rf_rec / (rf_prec + rf_rec)
	if rf_f1 > best_f1:
		best_f1 = rf_f1
		best_model = 'Random Forest'

	lr_prec /= n_folds
	lr_rec /= n_folds
	lr_f1 = 2 * lr_prec * lr_rec / (lr_prec + lr_rec)
	if lr_f1 > best_f1:
		best_f1 = lr_f1
		best_model = 'Logistic Regression'
	
	svm_prec /= n_folds
	svm_rec /= n_folds
	svm_f1 = 2 * svm_prec * svm_rec / (svm_prec + svm_rec)
	if svm_f1 > best_f1:
		best_f1 = svm_f1
		best_model = 'SVM'
	
	print('Decision Tree:', dt_prec, dt_rec)
	print('Random Forest:', rf_prec, rf_rec)
	print('Logistic Regression:', lr_prec, lr_rec)
	print('SVM:', svm_prec, svm_rec)
	print()
	print('Best model:', best_model)
	print('F1 score:', best_f1)
	print()
	return best_model


def train_model(algorithm, X_train, y_train):
	if algorithm == 'SVM':
		svm_clf = SVC(gamma='scale')
		svm_clf.fit(X_train, y_train)
		return svm_clf
	else:
		print('Unknown algorithm to build a model')
		return None


def evaluate_model(model, X_test_vec, X_test_str, y_test):
	y_pred = model.predict(X_test_vec)

	# White list the predictions
	for idx, x_str in zip(range(len(X_test_str)), X_test_str):
		if x_str in white_list:
			y_pred[idx] = 1
	
	precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')
	print('Model performance on test set:')
	print('Precision:\t', precision)
	print('Recall:\t\t', recall)
	print('F1:\t\t', f1)
	return precision, recall, f1
	

def main():
	dev_set, test_set = get_file_numbers()

	best_model = cross_validation(dev_set, 4)
	
	dev_dataset = label_dataset(dev_set, True)
	model = train_model(best_model, dev_dataset[0], dev_dataset[1])

	# Evaluate on test set
	test_dataset = label_dataset(test_set, True)
	print('## Evaluating on Test Set: ##')
	model_prec, model_rec, model_f1 = evaluate_model(model, test_dataset[0], test_dataset[2], test_dataset[1])


if __name__ == "__main__":
	main()
