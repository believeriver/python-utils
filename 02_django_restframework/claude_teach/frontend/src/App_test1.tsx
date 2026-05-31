import { useState } from "react";

const App = () => {
  // useState<型>(初期値)
  // [状態変数, 状態を更新する関数]
  const [count, setCount] = useState<number>(0);
  const [message, setMessage] = useState<string>("");

  return (
    <div style={{padding: '2rem'}}>
      <h1>Counter App</h1>
      {/* カウンター */}
      <section style={{marginTop: '2rem'}}>
        <h2>Counter</h2>
        <p>Count: {count}</p>
        <button onClick={() => setCount(count + 1)}>Increment</button>
        <button onClick={() => setCount(count - 1)}>Decrement</button>
        <button onClick={() => setCount(0)}>Reset</button>
      </section>

      {/* メッセージ入力 */}
      <section style={{ margin: '2rem'}}>
        <h2>Message Input</h2>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message"
        />
        <p>Message: {message}</p>
      </section>
    </div>
  )
}

export default App;