from ml.health_models import calculate_bmi, calorie_target, fitness_score


def test_bmi():
    result = calculate_bmi(70, 175)
    assert result.value == 22.9
    assert result.category == "Healthy range"


def test_calorie_target():
    result = calorie_target(30, "male", 70, 175, "moderate", "maintain")
    assert result.target_kcal == result.maintenance_kcal
    assert result.bmr_kcal > 0


def test_fitness_score_limits():
    assert fitness_score(0, 0, 0, 0) == 0
    assert fitness_score(10000, 45, 8, 2.5) == 100
