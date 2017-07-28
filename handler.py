import unzip_requirements

import boto
import flask
import base64

from flask import render_template, url_for
from lib.wkhtmltopdf import wkhtmltopdf
from boto.s3.connection import ProtocolIndependentOrdinaryCallingFormat

app = flask.Flask('my app')

def generate_certificate(event, context):
    print("Generating certificate for {event}".format(event = event))
    user_id = event["user_id"]

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

        local_html_file_name = "/tmp/{file_name}.html".format(file_name = user_id)
        with open(local_html_file_name, "wb") as file:
            file.write(rendered.encode('utf-8'))

        local_pdf_file_name = "/tmp/{file_name}.pdf".format(file_name = user_id)
        wkhtmltopdf(local_html_file_name, local_pdf_file_name)

        bucket_name = "training-certificates.neo4j.com"

        s3_connection = boto.connect_s3(calling_format=ProtocolIndependentOrdinaryCallingFormat())
        bucket = s3_connection.get_bucket(bucket_name, validate=False)
        key = boto.s3.key.Key(bucket, "{user_id}.pdf".format(user_id=event["user_id"]))
        key.set_contents_from_filename(local_pdf_file_name)
        print("https://s3.amazonaws.com/{bucket_name}/{user_id}.pdf".format(bucket_name = bucket_name, user_id = user_id))
