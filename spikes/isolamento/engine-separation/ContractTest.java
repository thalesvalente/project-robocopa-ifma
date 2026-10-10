import com.google.gson.*;
import java.io.*;

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
        good(()->{var x=fresh().inbound(hello());if(!x.get("secret").getAsString().equals("backend"))throw new AssertionError();});
        bad(()->fresh().inbound(hello().replace("front","wrong")));
        bad(()->fresh().inbound(hello().replace("session\"","other\"")));
        bad(()->fresh().inbound(hello().replace("Walls","Spin Bot")));
        bad(()->fresh().inbound(hello().replace("1.0","2.0")));
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
