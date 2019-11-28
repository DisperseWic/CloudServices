FROM openjdk:8-jdk-alpine
VOLUME /tmp
WORKDIR /
ADD ./target/restservice-0.0.1-SNAPSHOT.jar /restservice-0.0.1-SNAPSHOT.jar
EXPOSE 8080
ENTRYPOINT ["java","-jar","/restservice-0.0.1-SNAPSHOT.jar"]
