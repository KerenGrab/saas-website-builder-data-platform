import pytest

from pipeline import db


pytestmark = pytest.mark.integration


class ForcedTestFailure(RuntimeError):
    pass


def _counts(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM public.part9f_test_parent"
        )
        parent_count = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*) FROM public.part9f_test_child"
        )
        child_count = cursor.fetchone()[0]

    return parent_count, child_count


def test_successful_atomic_work_commits(
    test_db_connection,
    clean_test_state,
):
    def work(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.part9f_test_parent (id, value)
                VALUES ('P1', 'parent')
                """
            )
            cursor.execute(
                """
                INSERT INTO public.part9f_test_child (id, parent_id, value)
                VALUES ('C1', 'P1', 'child')
                """
            )
        return "done"

    result = db.run_atomic(
        test_db_connection,
        work,
    )

    assert result == "done"
    assert _counts(test_db_connection) == (1, 1)


def test_forced_failure_rolls_back_all_writes(
    test_db_connection,
    clean_test_state,
):
    def work(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.part9f_test_parent (id, value)
                VALUES ('P1', 'parent')
                """
            )
            cursor.execute(
                """
                INSERT INTO public.part9f_test_child (id, parent_id, value)
                VALUES ('C1', 'P1', 'child')
                """
            )

        raise ForcedTestFailure(
            "forced failure after two writes"
        )

    with pytest.raises(ForcedTestFailure):
        db.run_atomic(
            test_db_connection,
            work,
        )

    assert _counts(test_db_connection) == (0, 0)
