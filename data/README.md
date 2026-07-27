# 📂 Where to put your Kaggle datasets

This app trains 4 real machine-learning models on 4 real Kaggle datasets.
Download each one below and drop the file **directly into this `data/`
folder** (no need to rename it, no need to unzip into subfolders — just the
data file itself). Both `.csv` and `.xlsx` are supported.

| # | Dataset | Kaggle link | Used for | Algorithm |
|---|---|---|---|---|
| 1 | **Obesity Levels** (eating habits & physical condition) | https://www.kaggle.com/datasets/fatemehmehrparvar/obesity-levels | Predicting obesity level (7 categories) | `RandomForestClassifier` |
| 2 | **Diabetes Prediction Dataset** | https://www.kaggle.com/datasets/iammustafatz/diabetes-prediction-dataset | Diabetes risk (Low/Medium/High) | `LogisticRegression` |
| 3 | **Sleep Health and Lifestyle Dataset** | https://www.kaggle.com/datasets/uom190346a/sleep-health-and-lifestyle-dataset | Sleep disorder prediction | `KNeighborsClassifier` |
| 4 | **Calories Burnt Prediction** | https://www.kaggle.com/datasets/ruchikakumbhar/calories-burnt-prediction | Calories burnt during exercise | `GradientBoostingRegressor` |

## How to download from Kaggle

1. You need a free Kaggle account (sign up at kaggle.com if you don't have one).
2. Click each link above → click the **Download** button on the dataset page.
3. Kaggle usually gives you a `.zip` file — unzip it. Inside you'll find one
   or more `.csv` files.
4. Copy the `.csv` file(s) into this folder: `health_fitness_digital_twin/data/`

That's it — you do **not** need to rename the files. The app automatically
scans this folder and matches each file to the right model by looking at
its column names.

## After placing the files

From the project root, run:
```bash
python -m ml.train_kaggle_models
```
This trains all 4 models and saves them to `ml/models/`. Then, to see
accuracy/precision/recall/F1 (classifiers) or MAE/RMSE/R² (regressor)
using an 80:20 split **and** 5-fold cross-validation:
```bash
python -m ml.evaluate_models
```
This prints a full report and also saves it to `ml/evaluation_report.txt`.

## What if I only download some of them?

That's fine — `train_kaggle_models.py` trains whichever datasets it finds
and skips the rest with a clear message. The app automatically falls back
to its built-in synthetic-data models for anything you haven't added yet,
so it always runs, no matter how many datasets you've downloaded.

## Expected columns (for reference / troubleshooting)

If a dataset doesn't get picked up, double check it has these columns
(exact Kaggle files already do — this is just for if you re-export or edit them):

- **Obesity Levels**: `Gender, Age, Height, Weight, family_history_with_overweight, FAVC, FCVC, NCP, CAEC, SMOKE, CH2O, SCC, FAF, TUE, CALC, MTRANS, NObeyesdad`
- **Diabetes Prediction**: `gender, age, hypertension, heart_disease, smoking_history, bmi, HbA1c_level, blood_glucose_level, diabetes`
- **Sleep Health**: `Gender, Age, Occupation, Sleep Duration, Quality of Sleep, Physical Activity Level, Stress Level, BMI Category, Blood Pressure, Heart Rate, Daily Steps, Sleep Disorder`
- **Calories Burnt**: `Gender, Age, Height, Weight, Duration, Heart_Rate, Body_Temp, Calories`
