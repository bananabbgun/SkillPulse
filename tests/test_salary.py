from skillpulse.schema import SalaryPeriod, parse_salary


def test_parse_negotiable_salary():
    salary = parse_salary("面議")
    assert salary.salary_known is False
    assert salary.monthly_point is None


def test_parse_monthly_range():
    salary = parse_salary("月薪 40,000~60,000 元")
    assert salary.salary_known is True
    assert salary.period == SalaryPeriod.monthly
    assert salary.monthly_min == 40000
    assert salary.monthly_max == 60000
    assert salary.monthly_point == 50000


def test_parse_yearly_salary_to_monthly():
    salary = parse_salary("年薪 1,200,000 元")
    assert salary.salary_known is True
    assert salary.period == SalaryPeriod.yearly
    assert salary.monthly_point == 100000


def test_parse_open_ended_monthly_salary():
    salary = parse_salary("月薪 55000元以上")
    assert salary.salary_known is True
    assert salary.monthly_min == 55000
    assert salary.monthly_max is None
    assert salary.monthly_point == 55000
