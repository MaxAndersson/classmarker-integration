import util.neo4j_accounts as accts

record_attempt_query = """
MERGE (u:User {auth0_key:{auth0_key}})
ON CREATE
SET u.email={email},
    u.firstName={given_name},
    u.lastName={family_name}
MERGE (e:Exam {id: [{auth0_key}, toString({test_id}), toString({date})] })
ON CREATE SET 
    e:Certification,
    e.finished={date},
    e.percent={score_percentage},
    e.points={score_absolute},
    e.maxPoints={score_maximum},
    e.testTakerName={name},
    e.passed={passed},
    e.name={test_name_short},
    e.testId={test_id}
MERGE (u)-[:TOOK]->(e)
RETURN e
"""


def record_attempt(db_driver, event):
    test_data = event

    profile = accts.get_profile(event['auth0_key'])
    print(profile)

    test_data["given_name"] = profile.get("given_name")
    test_data["family_name"] = profile.get("family_name")

    print(record_attempt_query)
    with db_driver.session() as session:
        results = session.write_transaction(lambda tx: tx.run(record_attempt_query, parameters=test_data))
        results.consume()


record_success_query = """\
MATCH (c:Certification) 
WITH max(c.certificateNumber) AS maxCertificateNumber
WITH maxCertificateNumber + round(rand() * 150) AS certificateNumber
MATCH (e:Exam {id: [{auth0_key}, {test_id}, {date}] })
SET e.certificateNumber = coalesce(e.certificateNumber, certificateNumber),
    e.certificatePath = {certificate}
RETURN e.certificateNumber AS certificateNumber  
"""


def record_success(db_driver, event):
    params = {
        "certificate": event["certificate"],
        "auth0_key": event["auth0_key"],
        "test_id": str(event["test_id"]),
        "date": str(event["date"])
    }

    print(record_success_query)
    print(event)
    print(params)

    with db_driver.session() as session:
        results = session.write_transaction(lambda tx: tx.run(record_success_query, parameters=params))
        return [{"certificate_number": record["certificateNumber"]} for record in results]


assign_swag_query = """
MATCH (u:User {auth0_key:{auth0_key}})
WHERE SIZE( (u)<-[:ISSUED_TO]-() ) = 0
WITH u LIMIT 1
MATCH (src:SwagRedemptionCode)
WHERE
  src.redeemed=false
  AND
  src.type='certified'
  AND
  size( (src)-[:ISSUED_TO]->(:User) ) = 0
WITH u, src
LIMIT 1
MERGE (src)-[:ISSUED_TO]->(u)
"""


def assign_swag_code(db_driver, auth0_key):
    print(assign_swag_query)
    with db_driver.session() as session:
        results = session.run(assign_swag_query, parameters={"auth0_key": auth0_key})
        results.consume()


unsent_swag_emails_query = """
MATCH (u:User)<-[:ISSUED_TO]-(swag)
where exists(u.auth0_key) 
AND exists(u.firstName)
AND exists(u.lastName)
AND not exists(swag.email_sent)
// return u.firstName AS firstName, u.lastName AS lastName, swag.code AS swagCode, u.email as email
return u.firstName AS firstName, u.lastName AS lastName, swag.code AS swagCode, "m.h.needham@gmail.com" as email
"""


def find_unsent_swag_emails(db_driver):
    with db_driver.session() as session:
        results = session.run(unsent_swag_emails_query)

        return [{"first_name": record["firstName"],
                 "last_name": record["lastName"],
                 "swag_code": record["swagCode"],
                 "email": record["email"]}
                for record in results]


mark_swag_email_sent_query = """
MATCH (s:SwagRedemptionCode { code: {swag_code} })
SET s.email_sent = true
"""


def swag_email_sent(db_driver, swag_code):
    print("Marking swag email sent " + swag_code)
    with db_driver.session() as session:
        results = session.run(mark_swag_email_sent_query, parameters={"swag_code": swag_code})
        results.consume()
