FROM kbase/sdkbase2:python
MAINTAINER Sean Jungbluth <sjungbluth@lbl.gov>
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

WORKDIR /kb/module/bin

# To install all the dependencies
RUN apt-get update && apt-get install -y wget tzdata git r-base gcc automake libtool libc6-dev libssl-dev curl libcurl4-openssl-dev bowtie2

# install perl and packages
RUN conda install -c bioconda perl-bioperl

RUN cpan -i App::cpanminus && cpanm -i Excel::Writer::XLSX && cpanm -i Array::Split && cpanm -i Parallel::ForkManager

# install R packages
RUN echo "install.packages(\"tidyverse\", repos=\"http://cran.us.r-project.org\")" | R --no-save && \
    echo "install.packages(\"diagram\", repos=\"http://cran.us.r-project.org\")" | R --no-save && \
    echo "install.packages(\"forcats\", repos=\"http://cran.us.r-project.org\")" | R --no-save && \
    echo "install.packages(\"reshape2\", repos=\"http://cran.us.r-project.org\")" | R --no-save && \
    echo "install.packages(\"digest\", repos=\"http://cran.us.r-project.org\")" | R --no-save && \
    echo "install.packages(\"htmltools\", repos=\"http://cran.us.r-project.org\")" | R --no-save && \
    echo "install.packages(\"rmarkdown\", repos=\"http://cran.us.r-project.org\")" | R --no-save && \
    echo "install.packages(\"reprex\", repos=\"http://cran.us.r-project.org\")" | R --no-save && \
    echo "install.packages(\"stringi\", repos=\"http://cran.us.r-project.org\")" | R --no-save && \
    echo "install.packages(\"ggthemes\", repos=\"http://cran.us.r-project.org\")" | R --no-save && \
    echo "install.packages(\"ggalluvial\", repos=\"http://cran.us.r-project.org\")" | R --no-save

RUN mv /miniconda/lib/libgfortran.so.4.0.0 /miniconda/lib/libgfortran.so.4.0.0.bk && \
    echo "install.packages(\"ggraph\", repos=\"http://cran.us.r-project.org\")" | R --no-save

RUN pip install pandas

RUN conda install -c bioconda sambamba

RUN conda install -c bioconda bamtools

RUN wget https://github.com/wwood/CoverM/releases/download/v0.3.1/coverm-x86_64-unknown-linux-musl-0.3.1.tar.gz && tar -xvf coverm-x86_64-unknown-linux-musl-0.3.1.tar.gz && mv coverm-x86_64-unknown-linux-musl-0.3.1/coverm /usr/local/bin/ && cd ../ && rm -rf coverm-*

RUN wget http://eddylab.org/software/hmmer3/3.1b2/hmmer-3.1b2-linux-intel-x86_64.tar.gz && tar -xvzf hmmer-3.1b2-linux-intel-x86_64.tar.gz && cd hmmer-3.1b2-linux-intel-x86_64 && ./configure && make && make install && cd ../ && rm -rf hmmer-3.1b2-*

RUN wget https://github.com/hyattpd/Prodigal/releases/download/v2.6.3/prodigal.linux && mv prodigal.linux /usr/local/bin/prodigal && chmod +x /usr/local/bin/prodigal

# unclear why diamond is needed, but it is among the first steps run with the test data and throws a non-critical error if not installed
RUN wget http://github.com/bbuchfink/diamond/releases/download/v0.9.27/diamond-linux64.tar.gz && tar xzf diamond-linux64.tar.gz && mv diamond /usr/local/bin/ && rm diamond-linux64.tar.gz

# hack to change these scripts to use anaconda version of perl (with all installed dependencies)
RUN git clone https://github.com/AnantharamanLab/METABOLIC.git && cd METABOLIC && sed -i 's/.usr.bin.perl/\/usr\/bin\/env perl/' METABOLIC-C.pl && sed -i 's/.usr.bin.perl/\/usr\/bin\/env perl/' METABOLIC-G.pl

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

ENV PATH=/kb/module/lib/kb_metabolic/bin/bbmap:$PATH
ENV PATH=/kb/module/lib/kb_metabolic/bin/samtools/bin:$PATH

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
