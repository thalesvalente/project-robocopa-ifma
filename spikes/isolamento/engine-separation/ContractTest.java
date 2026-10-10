import com.google.gson.*;
import java.io.*;
import org.java_websocket.handshake.HandshakeImpl1Client;
import org.java_websocket.enums.HandshakeState;

/** Executed before Docker integration; pure gateway state-machine tests. */
public final class ContractTest {
    interface Case{void run()throws Exception;}
    static int passed=0;
    static void good(Case c)throws Exception{c.run();passed++;}
    static void bad(Case c)throws Exception{try{c.run();throw new AssertionError("EXPECTED_DENIAL");}catch(IOException expected){passed++;}}
    static ProtocolGate.Rule fresh(){var r=new ProtocolGate.Rule("Walls","front","backend");r.session="session";return r;}
    static String hello(){return "{\"type\":\"BotHandshake\",\"name\":\"Walls\",\"version\":\"1.0\",\"sessionId\":\"session\",\"secret\":\"front\",\"authors\":[\"fixture\"]}";}
    static ProtocolGate.Rule auth()throws Exception{var r=fresh();r.inbound(hello());return r;}
    public static void main(String[] args)throws Exception{
        good(()->{
            var env=Probe.officialEnvironment("ws://127.0.0.1:8765","front-fixture");
            if(env.size()!=2 || !"front-fixture".equals(env.get("SERVER_SECRET"))
                || !"ws://127.0.0.1:8765".equals(env.get("SERVER_URL")) || env.containsKey("ADMIN_SECRET"))
                throw new AssertionError("OFFICIAL_BOT_ENVIRONMENT");
        });
        good(()->{
            var h=new HandshakeImpl1Client();h.setResourceDescriptor("/");h.put("Sec-WebSocket-Version","13");
            if(ProtocolGate.draft().acceptHandshakeAsServer(h)!=HandshakeState.MATCHED)throw new AssertionError("RFC6455_DEFAULT_PROTOCOL");
        });
        good(()->{var x=fresh().inbound(hello());if(!x.get("secret").getAsString().equals("backend"))throw new AssertionError();});
        bad(()->fresh().inbound(hello().replace("front","wrong")));
        bad(()->fresh().inbound(hello().replace("session\"","other\"")));
        bad(()->fresh().inbound(hello().replace("Walls","Spin Bot")));
        bad(()->fresh().inbound(hello().replace("1.0","2.0")));
        bad(()->fresh().inbound(hello().replace("\"authors\":[\"fixture\"]","\"isDroid\":\"false\"")));
        for(String type:new String[]{"ControllerHandshake","ObserverHandshake","StartGame","PauseGame","StopGame","ResumeGame","ChangeTps","NextTurn","EnableDebugMode","BotPolicyUpdate"}){
            bad(()->fresh().inbound("{\"type\":\""+type+"\"}"));
            bad(()->auth().inbound("{\"type\":\""+type+"\"}"));
        }
        bad(()->auth().inbound(hello()));
        good(()->auth().inbound("{\"type\":\"BotReady\"}"));
        good(()->auth().inbound("{\"type\":\"BotIntent\",\"targetSpeed\":6,\"turnRate\":8,\"firepower\":2}"));
        bad(()->auth().inbound("{\"type\":\"BotIntent\",\"command\":\"unexpected\"}"));
        bad(()->auth().inbound("{\"type\":\"BotIntent\",\"firepower\":100}"));
        bad(()->auth().inbound("{\"type\":\"BotIntent\",\"targetSpeed\":true}"));
        bad(()->auth().inbound("{\"type\":\"BotIntent\",\"targetSpeed\":1e999}"));
        bad(()->auth().inbound("{\"type\":\"BotIntent\",\"type\":\"PauseGame\"}"));
        bad(()->fresh().inbound(" ".repeat(20000)+hello()));
        bad(()->Wire.parse("[1,2]",100));
        bad(()->Wire.parse("{\"a\":"+"[".repeat(12)+"1"+"]".repeat(12)+"}",1000));
        good(()->{var x=auth().inbound("{\"type\":\"BotIntent\",\"stdOut\":\"not persisted\"}");if(x.has("stdOut"))throw new AssertionError();});
        System.out.println("{\"gateway_contract_cases\":"+passed+",\"status\":\"PASS\"}");
    }
}
