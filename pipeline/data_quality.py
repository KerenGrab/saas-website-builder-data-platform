"""Read-only Data Quality execution for Part 9E."""

from pipeline.dq_rules import DQ_RULES


SAMPLE_LIMIT = 5


def _count_violations(cursor, violation_sql):
    query = f"""
        SELECT COUNT(*)
        FROM (
            {violation_sql}
        ) AS violations
    """

    cursor.execute(query)

    return cursor.fetchone()[0]


def _fetch_samples(cursor, violation_sql):
    query = f"""
        SELECT *
        FROM (
            {violation_sql}
        ) AS violations
        LIMIT %s
    """

    cursor.execute(
        query,
        (SAMPLE_LIMIT,),
    )

    column_names = [
        column.name
        for column in cursor.description
    ]

    return [
        dict(zip(column_names, row))
        for row in cursor.fetchall()
    ]


def run_data_quality_checks(connection):
    """Execute DQ rules inside one read-only transaction."""
    if not connection.autocommit:
        raise RuntimeError(
            "9E DQ requires a connection "
            "opened with autocommit=True."
        )

    results = []

    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                "SET TRANSACTION READ ONLY"
            )

        for rule in DQ_RULES:
            with connection.cursor() as cursor:
                violation_count = (
                    _count_violations(
                        cursor,
                        rule["violation_sql"],
                    )
                )

                samples = []

                if violation_count > 0:
                    samples = _fetch_samples(
                        cursor,
                        rule["violation_sql"],
                    )

            status = (
                "PASS"
                if violation_count == 0
                else "FAIL"
            )

            result = {
                "rule_id": rule["rule_id"],
                "name": rule["name"],
                "domain": rule["domain"],
                "status": status,
                "violation_count": violation_count,
                "samples": samples,
            }

            results.append(result)

            print(
                f"{rule['rule_id']}: "
                f"{status} "
                f"({violation_count} violations)"
            )

            if samples:
                print(
                    "  Sample violations:"
                )

                for sample in samples:
                    print(
                        f"    {sample}"
                    )

    pass_count = sum(
        result["status"] == "PASS"
        for result in results
    )

    fail_count = (
        len(results)
        - pass_count
    )

    return {
        "results": results,
        "rules_executed": len(results),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "total_violations": sum(
            result["violation_count"]
            for result in results
        ),
    }

def exit_code_from_summary(summary):
    """Return the canonical Part 9E process code for a completed DQ run."""
    fail_count = summary.get("fail_count")

    if not isinstance(fail_count, int) or fail_count < 0:
        raise ValueError(
            "DQ summary must contain a non-negative integer fail_count."
        )

    return 0 if fail_count == 0 else 2
