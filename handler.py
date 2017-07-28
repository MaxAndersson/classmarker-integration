import boto
import flask
import base64

from flask import render_template, url_for
from lib.wkhtmltopdf import wkhtmltopdf

app = flask.Flask('my app')

def generate_certificate(event, context):
    print("Generating certificate for {event}".format(event = event))

    with app.app_context():
        with open("static/neo4j.png", "rb") as neo4j_image:
            base_64_image = base64.b64encode(neo4j_image.read())

        rendered = render_template('certificate.html', \
            base_64_image = base_64_image.decode("utf-8"), \
            name = event["name"], \
            test_name = "Neo4j Certification", \
            score_percentage = event["score_percentage"], \
            score_absolute = event["score_absolute"], \
            score_maximum = event["score_maximum"], \
            date = event["date"])

        local_html_file_name = "/tmp/{file_name}.html".format(file_name=event["user_id"])
        with open(local_html_file_name, "wb") as file:
            file.write(rendered.encode('utf-8'))

        local_pdf_file_name = "/tmp/{file_name}.pdf".format(file_name=event["user_id"])
        wkhtmltopdf(local_html_file_name, local_pdf_file_name)


        # s3_connection = boto.connect_s3()
        # bucket = s3_connection.get_bucket(short_name)
        # key = boto.s3.key.Key(bucket, "{summary}.html".format(summary=short_name))
        # key.set_contents_from_filename(local_file_name)
