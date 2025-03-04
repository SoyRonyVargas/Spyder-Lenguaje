import { OnChange } from '@monaco-editor/react'
import axios from 'axios'
import { useEffect, useState } from 'react'
const APIURL = 'http://127.0.0.1:5000/compile'

type Token = [string, string]

type Compiled = {
    message: string
    tokens_found: Token[]
    variables: object
    minified_code: string
}

const useCompile = () => {

    const [ error , setError ] = useState<string | null>(null)
    const [ success , setSuccess ] = useState<Compiled | null>(null)
    const [ value , setValue ] = useState<any>('')
    const [ variables , setVariables ] = useState<any>([])

    useEffect(() => {
        const code = window.localStorage.getItem('code')
        if(code) {
            (document.getElementById('code') as HTMLInputElement).value = code
            setValue(code)
        }
    }
    , [])
    const handleCompile = async () => {


        try 
        {

            const code = value as string

            const { data } = await axios.post(APIURL, { code })

            const { variables } = data
            const { __funciones__ , __logs__ , ...rest } = variables

            setSuccess(data)
            setVariables(rest)

            setError(null)
        
        } 
        catch (error) 
        {
            console.log('Error:', error)
            handleError(error)    
        }

    }

    const handleError = (error: any) => {

        setSuccess(null)

        if( error.response ) 
        {
            setError(error?.response?.data?.error)
        }

    }

    const handleChangeCode = (event: OnChange) => {
        console.log(event);
        const newCode:any = event;
        window.localStorage.setItem('code', newCode);
        setValue(newCode)
    };

  return {
    handleChangeCode,
    handleCompile,
    variables,
    success,
    error,
    value,
  }
}

export default useCompile