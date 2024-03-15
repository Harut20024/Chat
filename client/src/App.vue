<template>
  <div id="app">
    <div v-if="!nameEntered">
      <input
        @keyup.enter="registerUser"
        v-model="name"
        placeholder="Enter your name"
      />
      <button @click="registerUser">Enter Chat</button>
    </div>
    <div v-else>
      <h1>Real-time Chat</h1>
      <div>
        <h2>Online Users:</h2>
        <div id="online-users">
          <span v-for="user in onlineUsers" :key="user.sid">{{
            user.name
          }}</span>
        </div>
      </div>

      <input
        v-model="message"
        placeholder="Write a message"
        @keyup.enter="sendMessage"
      />
      <button @click="sendMessage">Send</button>
      <ul>
        <li
          v-for="(msg, index) in messages"
          :key="index"
          :class="{
            'my-message': isMyMessage(msg),
            'other-message': !isMyMessage(msg),
          }"
        >
          {{ msg }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import io from "socket.io-client";
import CryptoJS from "crypto-js";

export default {
  name: "App",
  data() {
    return {
      message: "",
      messages: [],
      name: "",
      nameEntered: false,
      onlineUsers: [],
      socket: null,
    };
  },
  created() {
    this.loadMessages();
    this.connectToSocket();
  },
  methods: {
    connectToSocket() {
      this.socket = io("http://localhost:5000");
      this.socket.on("receive_message", (msg) => {
        if (!this.isMessageStored(msg)) {
          this.messages.push(msg);
          this.storeMessages();
        }
      });

      this.socket.on("users_online", (users) => {
        this.onlineUsers = users;
      });
      this.socket.on("user_joined", (name) => {
        console.log(`${name} joined the chat.`);
      });
      this.socket.on("user_left", (name) => {
        console.log(`${name} left the chat.`);
      });
    },
    registerUser() {
      if (this.name.trim()) {
        this.socket.emit("register_user", this.name);
        this.nameEntered = true;
      }
    },
    isMessageStored(msg) {
      return this.messages.includes(msg);
    },
    sendMessage() {
      if (this.name.trim() && this.message.trim()) {
        this.socket.emit("send_message", {
          message: this.message,
          name: this.name,
        });
        this.message = "";
      }
    },
    storeMessages() {
      const encryptedMessages = CryptoJS.AES.encrypt(
        JSON.stringify(this.messages),
        "secret key"
      ).toString();
      localStorage.setItem("messages", encryptedMessages);
    },
    loadMessages() {
      const encryptedMessages = localStorage.getItem("messages");
      if (encryptedMessages) {
        const bytes = CryptoJS.AES.decrypt(encryptedMessages, "secret key");
        const decryptedMessages = JSON.parse(bytes.toString(CryptoJS.enc.Utf8));
        this.messages = decryptedMessages;
      }
    },
    isMyMessage(msg) {
      const senderName = msg.split(":")[0].trim();
      return this.name === senderName;
    },
  },
};
</script>

<style scoped>
@import "./assets/style.css";
</style>
