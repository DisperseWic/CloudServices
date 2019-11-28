package com.example.restservice.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.atomic.AtomicLong;

@RestController
public class HelloWorld {
    AtomicLong count = new AtomicLong(0);

    @RequestMapping("/get")
    String hello() {
        return count.toString();
    }
    @RequestMapping("/increment")
    void increment(){
        count.getAndIncrement();
    }
}
