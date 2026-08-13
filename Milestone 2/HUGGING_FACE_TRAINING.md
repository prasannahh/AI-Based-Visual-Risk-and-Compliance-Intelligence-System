# Hugging Face dataset training

Run the data-backed version of the application:

```powershell
cd "Milestone 2"
streamlit run app_hf.py
```

Select **Download dataset and train model**. The app downloads the public [mnemoraorg/calorie-burnt-15k](https://huggingface.co/datasets/mnemoraorg/calorie-burnt-15k) source files, merges `raw_exercise.csv` with `raw_calories.csv` by `User_ID`, and saves the trained model at `models/hf_calorie_predictor.joblib`.

The model predicts workout calorie expenditure from demographic and exercise-session measurements. The daily calorie target shown by the app is still an explainable Mifflin–St Jeor calculation, because the dataset contains exercise-calorie labels, not individual daily calorie requirements or longitudinal weight outcomes.
