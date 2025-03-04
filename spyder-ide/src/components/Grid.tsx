import useCompile from '../hooks/useCompile'
import Editor from '@monaco-editor/react';

const Grid = () => {

    const {
        handleChangeCode,
        handleCompile,
        success,
        variables,
        error,
        value
    } = useCompile()
    return (
        <div className='grid'>
            <section>
                <Editor 
                    height="500px" 
                    // language="javascript"  
                    value={value}
                    theme='vs-dark'
                    options={{ minimap: { enabled: true } }}
                    language="plaintext" // Modo texto plano (sin resaltado)
                    onChange={handleChangeCode}

                />
                <textarea 
                    id="code"
                    style={{display: 'none'}}
                    // onInput={handleChangeCode}
                    // onChange={handleChangeCode}
                >
                </textarea>
                <button onClick={handleCompile} className='btn btn-primary'>Compilar</button>
                <section>
                <h3>Consola</h3>
                {
                    error
                    && 
                    <div className="alert alert-danger" role="alert">
                        {error}
                    </div>
                }
                {
                    success
                    && 
                    <div className="alert alert-success" role="alert">
                        {success.message}
                    </div>
                }
            </section>
            </section>
            <section>
                <div>
                    <h3>Tokens detectados</h3>
                        {
                            success &&
                            <ol className='box-tokens'>
                            {success?.tokens_found.map((token, index) => (
                                <li key={index}>{token[0]} - {token[1]}</li>
                            ))}
                            </ol>
                        }
                </div>
                <div>
                    <h3>Variables</h3>
                    {
                        success &&
                        <ul>
                            {Object.entries(variables).map(([key, value], index) => (
                                <li key={index}>{key} - {value}</li>
                            ))}
                        </ul>
                    }
                </div>
                <div>
                    <h3>Codigo Final</h3>
                    {
                        success &&
                        success.minified_code
                    }
                </div>
                <hr />
                <div>
                    <h3>Logs</h3>
                    <ul className='box-tokens'>
                        {
                            success &&
                            success.logs.map( log => (
                                <>
                                    <li>
                                        {log}
                                    </li>
                                    {/* <hr /> */}
                                </>
                            ))
                        }
                    </ul>
                </div>
            </section>
           
        </div>
    )
}

export default Grid