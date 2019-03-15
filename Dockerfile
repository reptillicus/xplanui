FROM sd2e/python3:ubuntu17

MAINTAINER TACC-ACI-WMA <wma_prtl@tacc.utexas.edu>

EXPOSE 8000

RUN apt-get update

RUN pip install --upgrade pip

# for xplan_to_sbol
RUN apt-get -y install libxslt1-dev

# steel bank common lisp
RUN apt-get -y install sbcl
RUN apt-get -y install subversion
RUN apt-get -y install graphviz

#python 3 fork
RUN pip3 install --upgrade git+https://github.com/willblatt/pyDOE

# custom wheel for python3.6
RUN pip3 install https://github.com/tcmitchell/pySBOL/blob/ubuntu/Ubuntu_16.04_64_3/dist/pySBOL-2.3.0.post11-cp36-none-any.whl?raw=true

RUN pip3 install git+https://github.com/nroehner/pySBOLx git+https://github.com/sd2e/xplan_to_sbol git+https://github.com/SD2E/synbiohub_adapter


# add EPEL repo
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get -y install nodejs
# for xplan_to_sbol
RUN apt-get -y install libxslt1-dev

# steel bank common lisp
RUN apt-get -y install sbcl
RUN apt-get -y install subversion
RUN apt-get -y install graphviz

#python 3 fork
RUN pip3 install --upgrade git+https://github.com/willblatt/pyDOE

# custom wheel for python3.6
RUN pip3 install https://github.com/tcmitchell/pySBOL/blob/ubuntu/Ubuntu_16.04_64_3/dist/pySBOL-2.3.0.post11-cp36-none-any.whl?raw=true

RUN pip3 install git+https://github.com/nroehner/pySBOLx git+https://github.com/sd2e/xplan_to_sbol git+https://github.com/SD2E/synbiohub_adapter



#install uwsgi
RUN pip3 install --upgrade pip
RUN pip3 install uwsgi

# COPY server/requirements.txt /tmp/requirements.txt




COPY . /portal
RUN pip3 install /portal/xplan/xplan_api[dev]
WORKDIR /portal
RUN pip3 install -r /portal/requirements.txt

ENV XPLAN_PATH=/portal/xplan/xplan_api/xplan/

CMD /bin/bash
