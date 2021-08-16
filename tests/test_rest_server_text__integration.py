"""
Test the REST server's responses for the text algorithms in :mod:`algos.text` . This module depends on the use of
the pytest fixture rest_server which does the set-up/teardown for an actual instance of the rest server.
"""
import os
import textwrap
import threading
import subprocess
import time
import json
import pytest
from algosrest.server.main import app

from fastapi import Response
from fastapi.testclient import TestClient

client: TestClient = TestClient(app)


def start_server():
    """
    Start the server process in a separate thread.
    """
    print(os.getcwd())
    os.chdir("algosrest/server/")
    subprocess.Popen(["uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8081"],
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    os.chdir("../..")


@pytest.fixture(scope="class")
def rest_server():
    # Start the server in a thread.
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    # Sleep a bit.
    time.sleep(1)

    # Yield something to keep it going.
    yield 1

    # Shutdown the server.
    subprocess.check_output("curl -s http://localhost:8081/shutdown", shell=True)

    # Wait a bit.
    time.sleep(1)


class DataText:
    """
    Test data for text based algorithms. Contains lists of tuples of the form (inputs, expected). The data for the
    following functions is contained within

    +--------------------------------------+
    | anagrams                             |
    +--------------------------------------+

    """
    anagrams__expected = [
        (
            {'the', 'car', 'can', 'caused', 'a', 'and', 'during', 'cried', 'by', 'its', 'rat', 'bowel', 'drinking',
             'elbow', 'bending', 'that', 'while', 'an', 'thing', 'cider', 'like', 'pain', 'cat', 'which', 'in', 'this',
             'act', 'below', 'is', 'night', 'arc'},
            [['act', 'cat'], ['arc', 'car'], ['below', 'bowel', 'elbow'], ['cider', 'cried'], ['night', 'thing']]
        ),
        (
            {"elbow", "below", "bowel"},
            [['below', 'bowel', 'elbow']]
        ),
        (
            {""},
            []
        )
    ]
    """
    Test cases for :meth:`algosrest.server.text.TextREST.anagrams` ., testing that it functions correctly for 
    expected inputs.
    """

    anagrams__unexpected = [
        ({"noinput": "elbow below bowel"}, (400, {"detail": "'input' not found"})),
        ({"input": 1}, (400, {"detail": "Unsupported Type"}))
    ]
    """
    Test cases for :meth:`algosrest.server.text.TextREST.anagrams` ., testing that it raises HTTPExceptions for
    unexpected input.
    """


class TestText:
    """
    We use the pytest fixture rest_server which has class scope, so we need to group all our code together into one
    class, to prevent repeatedly starting up and shutting down the fastapi server, which can greatly increase
    the runtime of the tests.
    """
    @pytest.mark.parametrize(
        "test_input,expected",
        DataText.anagrams__expected,
        ids=[str(v) for v in range(len(DataText.anagrams__expected))]
    )
    def test_anagrams__expected(self, test_input, expected, rest_server):
        """
        Test the ``/text/anagrams`` endpoint with expected inputs. Uses :meth:`algosrest.server.text.TextREST.anagrams`
        """
        # Make the request and get the response.
        post_request = textwrap.dedent(
            f"""
            curl -s --header "Content-Type: application/json"   --request POST   
            --data '{json.dumps({"input": " ".join(list(test_input))})}'   http://localhost:8081/text/anagrams
            """
        ).replace("\n", " ")
        post_output: bytes = subprocess.check_output(post_request, shell=True)

        # Sort the output into the order the expected response expects.
        anagrams_found = json.loads(post_output.decode())
        anagrams_found = [sorted(x) for x in anagrams_found]
        anagrams_found.sort()

        assert anagrams_found == expected

    @pytest.mark.parametrize(
        "test_input,expected",
        DataText.anagrams__unexpected,
        ids=[repr(v) for v in DataText.anagrams__unexpected]
    )
    def test_anagrams__unexpected(self, test_input, expected, rest_server):
        """
        Test the ``/text/anagrams`` endpoint with expected inputs. Uses :meth:`algosrest.server.text.TextREST.anagrams`
        """
        # Make the request with the invalid input data
        post_request = textwrap.dedent(
            f"""
            curl -s --header "Content-Type: application/json"   --request POST   
            --data '{json.dumps(test_input)}'   http://localhost:8081/text/anagrams
            """
        ).replace("\n", " ")
        post_output: bytes = subprocess.check_output(post_request, shell=True)

        # Read back the error from the shell output
        error = json.loads(post_output.decode())

        # Check if the reason for the error is as expected.
        assert error == expected[1]