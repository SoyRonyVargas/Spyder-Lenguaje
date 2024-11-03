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

    useEffect(() => {
        const code = window.localStorage.getItem('code')
        if(code) {
            (document.getElementById('code') as HTMLInputElement).value = code
        }
    }
    , [])
    const handleCompile = async () => {


        try 
        {

            const code = (document.getElementById('code') as HTMLInputElement)?.value as string

            const { data } = await axios.post(APIURL, { code })

            setSuccess(data)

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

    const handleChangeCode = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newCode = event.target.value;
        window.localStorage.setItem('code', newCode);
    };

  return {
    handleChangeCode,
    handleCompile,
    error,
    success
  }
}

export default useCompile