import pytest

from pipeline import loading


pytestmark = pytest.mark.integration


def _count_rows(connection, table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) FROM public.{table_name}"
        )
        return cursor.fetchone()[0]


def test_non_empty_target_is_rejected_without_mutation(
    test_db_connection,
    clean_test_state,
):
    with test_db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.part9f_test_target (id, value)
            VALUES ('T1', 'already here')
            """
        )

    before = _count_rows(
        test_db_connection,
        "part9f_test_target",
    )

    with pytest.raises(loading.TargetNotEmptyError):
        loading.assert_target_is_empty(
            test_db_connection,
            target_tables=("part9f_test_target",),
        )

    after = _count_rows(
        test_db_connection,
        "part9f_test_target",
    )

    assert before == 1
    assert after == before
